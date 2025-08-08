import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/consultar', methods=['POST', 'OPTIONS'])
def consultar():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    data = request.get_json()
    rut = data.get('rut')
    if not rut:
        return _corsify_response(jsonify({'error': 'RUT no proporcionado'}), 400)

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT nombre, saldo FROM usuarios WHERE rut = %s", (rut,))
        res = cur.fetchone()
        if not res:
            cur.close()
            conn.close()
            return _corsify_response(jsonify({'error': 'RUT no encontrado'}), 404)

        cur.execute("SELECT tipo, cantidad, fecha FROM historial WHERE rut = %s ORDER BY fecha DESC", (rut,))
        historial = cur.fetchall()
        historial_data = [{'tipo': t, 'cantidad': c, 'fecha': f.isoformat()} for t, c, f in historial]

        cur.close()
        conn.close()
        return _corsify_response(jsonify({'nombre': res[0], 'saldo': res[1], 'historial': historial_data}))
    except Exception as e:
        return _corsify_response(jsonify({'error': str(e)}), 500)

@app.route('/registrar_impresion', methods=['POST', 'OPTIONS'])
def registrar_impresion():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    data = request.get_json()
    rut = data.get('rut')
    paginas = data.get('paginas')
    if not rut or paginas is None:
        return _corsify_response(jsonify({'error': 'Datos incompletos'}), 400)

    try:
        paginas = int(paginas)
    except:
        return _corsify_response(jsonify({'error': 'Páginas debe ser un número'}), 400)

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT saldo FROM usuarios WHERE rut = %s", (rut,))
        res = cur.fetchone()
        if not res:
            cur.close()
            conn.close()
            return _corsify_response(jsonify({'error': 'Usuario no encontrado'}), 404)

        saldo = res[0]
        if paginas > saldo:
            cur.close()
            conn.close()
            return _corsify_response(jsonify({'error': 'Saldo insuficiente'}), 400)

        nuevo_saldo = saldo - paginas
        cur.execute("UPDATE usuarios SET saldo = %s WHERE rut = %s", (nuevo_saldo, rut))
        cur.execute("INSERT INTO historial (rut, tipo, cantidad, fecha) VALUES (%s, %s, %s, %s)",
                    (rut, 'impresion', paginas, datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
        return _corsify_response(jsonify({'mensaje': 'Impresión registrada', 'nuevo_saldo': nuevo_saldo}))
    except Exception as e:
        return _corsify_response(jsonify({'error': str(e)}), 500)

@app.route('/cargar_usuario', methods=['POST', 'OPTIONS'])
def cargar_usuario():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    data = request.get_json()
    nombre = data.get('nombre')
    rut = data.get('rut')
    paginas = data.get('paginas')
    if not all([nombre, rut, paginas]):
        return _corsify_response(jsonify({'error': 'Faltan datos'}), 400)

    try:
        paginas = int(paginas)
    except:
        return _corsify_response(jsonify({'error': 'Paginas debe ser entero'}), 400)

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT saldo FROM usuarios WHERE rut = %s", (rut,))
        res = cur.fetchone()
        if res:
            nuevo_saldo = res[0] + paginas
            cur.execute("UPDATE usuarios SET saldo = %s WHERE rut = %s", (nuevo_saldo, rut))
        else:
            nuevo_saldo = paginas
            cur.execute("INSERT INTO usuarios (nombre, rut, saldo) VALUES (%s, %s, %s)", (nombre, rut, paginas))

        cur.execute("INSERT INTO historial (rut, tipo, cantidad, fecha) VALUES (%s, %s, %s, %s)",
                    (rut, 'recarga', paginas, datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
        return _corsify_response(jsonify({'mensaje': f'Saldo cargado exitosamente para {nombre}', 'nuevo_saldo': nuevo_saldo}))
    except Exception as e:
        return _corsify_response(jsonify({'error': str(e)}), 500)

@app.route('/get_usuarios', methods=['GET'])
def get_usuarios():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT nombre, rut, saldo FROM usuarios")
        rows = cur.fetchall()
        usuarios = [{'nombre': r[0], 'rut': r[1], 'saldo': r[2]} for r in rows]
        cur.close()
        conn.close()
        return _corsify_response(jsonify({'usuarios': usuarios}))
    except Exception as e:
        return _corsify_response(jsonify({'error': str(e)}), 500)

# Funciones CORS para manejar OPTIONS y cabeceras

def _build_cors_preflight_response():
    from flask import make_response
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
    return response

def _corsify_response(response, status=200):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, status

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
