from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3

app = Flask(__name__)

# Permitir solicitudes desde GitHub Pages con headers específicos
CORS(app, resources={r"/*": {"origins": "https://cybernovala.github.io"}},
     supports_credentials=True,
     allow_headers=["Content-Type"])

def init_db():
    with sqlite3.connect("usuarios.db") as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                rut TEXT NOT NULL UNIQUE,
                saldo INTEGER DEFAULT 200
            )
        ''')

init_db()

def cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "https://cybernovala.github.io"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route('/consultar', methods=['POST', 'OPTIONS'])
@app.route('/registrar_impresion', methods=['POST', 'OPTIONS'])
@app.route('/cargar_usuario', methods=['POST', 'OPTIONS'])
def handle_requests():
    if request.method == 'OPTIONS':
        return cors_response({}, 204)

    path = request.path
    data = request.get_json()
    rut = data.get('rut')

    if path == '/consultar':
        if not rut:
            return cors_response({'error': 'RUT no proporcionado'}, 400)
        with sqlite3.connect("usuarios.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, saldo FROM usuarios WHERE rut = ?", (rut,))
            res = cursor.fetchone()
        if res:
            return cors_response({'nombre': res[0], 'saldo': res[1]})
        else:
            return cors_response({'error': 'RUT no encontrado'}, 404)

    elif path == '/registrar_impresion':
        paginas = data.get('paginas')
        if not rut or paginas is None:
            return cors_response({'error': 'Datos incompletos'}, 400)
        try:
            paginas = int(paginas)
        except ValueError:
            return cors_response({'error': 'Páginas debe ser un número'}, 400)

        with sqlite3.connect("usuarios.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT saldo FROM usuarios WHERE rut = ?", (rut,))
            res = cursor.fetchone()
            if not res:
                return cors_response({'error': 'Usuario no encontrado'}, 404)
            saldo = res[0]
            if paginas > saldo:
                return cors_response({'error': 'Saldo insuficiente'}, 400)
            nuevo_saldo = saldo - paginas
            cursor.execute("UPDATE usuarios SET saldo = ? WHERE rut = ?", (nuevo_saldo, rut))
            conn.commit()
        return cors_response({'mensaje': 'Impresión registrada', 'nuevo_saldo': nuevo_saldo})

    elif path == '/cargar_usuario':
        nombre = data.get('nombre')
        paginas = data.get('paginas')
        if not all([nombre, rut, paginas]):
            return cors_response({'error': 'Faltan datos'}, 400)
        try:
            paginas = int(paginas)
        except ValueError:
            return cors_response({'error': 'Paginas debe ser entero'}, 400)

        with sqlite3.connect("usuarios.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT saldo FROM usuarios WHERE rut = ?", (rut,))
            res = cursor.fetchone()
            if res:
                nuevo_saldo = res[0] + paginas
                cursor.execute("UPDATE usuarios SET saldo = ? WHERE rut = ?", (nuevo_saldo, rut))
            else:
                cursor.execute("INSERT INTO usuarios (nombre, rut, saldo) VALUES (?, ?, ?)", (nombre, rut, paginas))
            conn.commit()
        return cors_response({'mensaje': f'Saldo cargado exitosamente para {nombre}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
