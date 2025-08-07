from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3

app = Flask(__name__)

# Permitir solo el frontend de GitHub Pages
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["https://cybernovala.github.io"]
    }
})

# Inicializar base de datos
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

# Función auxiliar para respuestas con CORS
def cors_response(data, status=200):
    response = make_response(jsonify(data), status)
    response.headers["Access-Control-Allow-Origin"] = "https://cybernovala.github.io"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.route('/consultar', methods=['POST', 'OPTIONS'])
def consultar():
    if request.method == 'OPTIONS':
        return cors_response({}, 204)

    data = request.get_json()
    rut = data.get('rut')
    if not rut:
        return cors_response({'error': 'RUT no proporcionado'}, 400)

    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, saldo FROM usuarios WHERE rut = ?", (rut,))
        resultado = cursor.fetchone()

    if resultado:
        nombre, saldo = resultado
        return cors_response({'nombre': nombre, 'saldo': saldo}, 200)
    else:
        return cors_response({'error': 'RUT no encontrado'}, 404)

@app.route('/registrar_impresion', methods=['POST', 'OPTIONS'])
def registrar_impresion():
    if request.method == 'OPTIONS':
        return cors_response({}, 204)

    data = request.get_json()
    rut = data.get('rut')
    paginas = data.get('paginas')

    if not rut or paginas is None:
        return cors_response({'error': 'Datos incompletos'}, 400)

    try:
        paginas = int(paginas)
    except ValueError:
        return cors_response({'error': 'El valor de páginas debe ser un número entero'}, 400)

    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT saldo FROM usuarios WHERE rut = ?", (rut,))
        resultado = cursor.fetchone()

        if not resultado:
            return cors_response({'error': 'Usuario no encontrado'}, 404)

        saldo_actual = resultado[0]
        if paginas > saldo_actual:
            return cors_response({'error': 'Saldo insuficiente'}, 400)

        nuevo_saldo = saldo_actual - paginas
        cursor.execute("UPDATE usuarios SET saldo = ? WHERE rut = ?", (nuevo_saldo, rut))
        conn.commit()

    return cors_response({
        'mensaje': 'Impresión registrada',
        'nuevo_saldo': nuevo_saldo
    }, 200)

@app.route('/cargar_usuario', methods=['POST', 'OPTIONS'])
def cargar_usuario():
    if request.method == 'OPTIONS':
        return cors_response({}, 204)

    data = request.get_json()
    nombre = data.get('nombre')
    rut = data.get('rut')
    paginas = data.get('paginas')

    if not all([nombre, rut, paginas]):
        return cors_response({'error': 'Faltan datos'}, 400)

    try:
        paginas = int(paginas)
        with sqlite3.connect("usuarios.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT saldo FROM usuarios WHERE rut = ?", (rut,))
            res = cursor.fetchone()

            if res:
                nuevo_saldo = res[0] + paginas
                cursor.execute("UPDATE usuarios SET saldo = ? WHERE rut = ?", (nuevo_saldo, rut))
            else:
                cursor.execute(
                    "INSERT INTO usuarios (nombre, rut, saldo) VALUES (?, ?, ?)",
                    (nombre, rut, paginas)
                )
            conn.commit()
        return cors_response({'mensaje': f'Saldo cargado exitosamente para {nombre}'}, 200)
    except Exception as e:
        return cors_response({'error': f'Error al cargar usuario: {str(e)}'}, 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
