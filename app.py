from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Variables de conexión - reemplaza con tus datos Neon
DB_HOST = os.getenv("DB_HOST", "tu_host_neon")
DB_NAME = os.getenv("DB_NAME", "tu_basedatos")
DB_USER = os.getenv("DB_USER", "tu_usuario")
DB_PASS = os.getenv("DB_PASS", "tu_password")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

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

    try:
        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        return cors_response({'error': f'Error de conexión a BD: {str(e)}'}, 500)

    if request.path == '/consultar':
        if not rut:
            return cors_response({'error': 'RUT no proporcionado'}, 400)
        cursor.execute("SELECT nombre, saldo_paginas FROM usuarios WHERE rut = %s", (rut,))
        res = cursor.fetchone()
        if not res:
            cursor.close()
            conn.close()
            return cors_response({'error': 'RUT no encontrado'}, 404)

        cursor.execute("SELECT tipo, cantidad, fecha FROM historial WHERE rut = %s ORDER BY fecha DESC", (rut,))
        historial = cursor.fetchall()
        historial_data = [{'tipo': t, 'cantidad': c, 'fecha': f.isoformat()} for t, c, f in historial]

        cursor.close()
        conn.close()
        return cors_response({'nombre': res[0], 'saldo': res[1], 'historial': historial_data})

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

        cursor.execute("SELECT saldo_paginas FROM usuarios WHERE rut = %s", (rut,))
        res = cursor.fetchone()
        if not res:
            cursor.close()
            conn.close()
            return cors_response({'error': 'Usuario no encontrado'}, 404)
        saldo = res[0]
        if paginas > saldo:
            cursor.close()
            conn.close()
            return cors_response({'error': 'Saldo insuficiente'}, 400)
        nuevo_saldo = saldo - paginas
        cursor.execute("UPDATE usuarios SET saldo_paginas = %s WHERE rut = %s", (nuevo_saldo, rut))
        cursor.execute(
            "INSERT INTO historial (rut, tipo, cantidad, fecha) VALUES (%s, %s, %s, %s)",
            (rut, 'impresion', paginas, datetime.now())
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

        cursor.execute("SELECT saldo_paginas FROM usuarios WHERE rut = %s", (rut,))
        res = cursor.fetchone()
        if res:
            nuevo_saldo = res[0] + paginas
            cursor.execute("UPDATE usuarios SET saldo_paginas = %s WHERE rut = %s", (nuevo_saldo, rut))
        else:
            cursor.execute(
                "INSERT INTO usuarios (nombre, rut, saldo_paginas) VALUES (%s, %s, %s)",
                (nombre, rut, paginas)
            )
        cursor.execute(
            "INSERT INTO historial (rut, tipo, cantidad, fecha) VALUES (%s, %s, %s, %s)",
            (rut, 'recarga', paginas, datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()
        return cors_response({'mensaje': f'Saldo cargado exitosamente para {nombre}'})

@app.route('/get_usuarios', methods=['GET'])
def get_usuarios():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, rut, saldo_paginas FROM usuarios")
        rows = cursor.fetchall()
        usuarios = [{'nombre': r[0], 'rut': r[1], 'saldo': r[2]} for r in rows]
        cursor.close()
        conn.close()
        return cors_response({'usuarios': usuarios})
    except Exception as e:
        return cors_response({'error': f'Error de conexión a BD: {str(e)}'}, 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
