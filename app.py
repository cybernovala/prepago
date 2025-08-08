from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Configuración de la conexión a Neon PostgreSQL
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', 5432)

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    return conn

def cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route('/consultar', methods=['POST', 'OPTIONS'])
@app.route('/registrar_impresion', methods=['POST', 'OPTIONS'])
@app.route('/cargar_usuario', methods=['POST', 'OPTIONS'])
def handle_requests():
    if request.method == 'OPTIONS':
        return cors_response({}, 204)

    data = request.get_json()
    rut = data.get('rut')

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.path == '/consultar':
        if not rut:
            cursor.close()
            conn.close()
            return cors_response({'error': 'RUT no proporcionado'}, 400)

        cursor.execute("SELECT id, nombre, saldo_paginas FROM usuarios WHERE rut = %s", (rut,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return cors_response({'error': 'RUT no encontrado'}, 404)

        user_id, nombre, saldo = user

        cursor.execute(
            "SELECT tipo, paginas, fecha FROM historial_impresiones WHERE usuario_id = %s ORDER BY fecha DESC",
            (user_id,)
        )
        historial = cursor.fetchall()
        historial_data = [{'tipo': t, 'cantidad': p, 'fecha': f.isoformat()} for t, p, f in historial]

        cursor.close()
        conn.close()

        return cors_response({'nombre': nombre, 'saldo': saldo, 'historial': historial_data})

    elif request.path == '/registrar_impresion':
        paginas = data.get('paginas')
        if not rut or paginas is None:
            cursor.close()
            conn.close()
            return cors_response({'error': 'Datos incompletos'}, 400)
        try:
            paginas = int(paginas)
        except ValueError:
            cursor.close()
            conn.close()
            return cors_response({'error': 'Páginas debe ser un número'}, 400)

        cursor.execute("SELECT id, saldo_paginas FROM usuarios WHERE rut = %s", (rut,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return cors_response({'error': 'Usuario no encontrado'}, 404)

        user_id, saldo = user

        if paginas > saldo:
            cursor.close()
            conn.close()
            return cors_response({'error': 'Saldo insuficiente'}, 400)

        nuevo_saldo = saldo - paginas
        cursor.execute("UPDATE usuarios SET saldo_paginas = %s WHERE id = %s", (nuevo_saldo, user_id))
        cursor.execute(
            "INSERT INTO historial_impresiones (usuario_id, tipo, paginas, fecha) VALUES (%s, %s, %s, %s)",
            (user_id, 'impresion', paginas, datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()
        return cors_response({'mensaje': 'Impresión registrada', 'nuevo_saldo': nuevo_saldo})

    elif request.path == '/cargar_usuario':
        nombre = data.get('nombre')
        paginas = data.get('paginas')
        if not all([nombre, rut, paginas]):
            cursor.close()
            conn.close()
            return cors_response({'error': 'Faltan datos'}, 400)
        try:
            paginas = int(paginas)
        except ValueError:
            cursor.close()
            conn.close()
            return cors_response({'error': 'Paginas debe ser entero'}, 400)

        cursor.execute("SELECT id, saldo_paginas FROM usuarios WHERE rut = %s", (rut,))
        user = cursor.fetchone()
        if user:
            user_id, saldo = user
            nuevo_saldo = saldo + paginas
            cursor.execute("UPDATE usuarios SET saldo_paginas = %s WHERE id = %s", (nuevo_saldo, user_id))
        else:
            cursor.execute(
                "INSERT INTO usuarios (nombre, rut, saldo_paginas) VALUES (%s, %s, %s)",
                (nombre, rut, paginas)
            )
            nuevo_saldo = paginas
            # Obtener el nuevo id insertado para historial
            cursor.execute("SELECT id FROM usuarios WHERE rut = %s", (rut,))
            user_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO historial_impresiones (usuario_id, tipo, paginas, fecha) VALUES (%s, %s, %s, %s)",
            (user_id, 'recarga', paginas, datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()
        return cors_response({'mensaje': f'Saldo cargado exitosamente para {nombre}'})

@app.route('/get_usuarios', methods=['GET'])
def get_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, rut, saldo_paginas FROM usuarios")
    rows = cursor.fetchall()
    usuarios = [{'nombre': r[0], 'rut': r[1], 'saldo': r[2]} for r in rows]
    cursor.close()
    conn.close()
    return cors_response({'usuarios': usuarios})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
