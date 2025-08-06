from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
# Permite CORS para cualquier origen en todas las rutas
CORS(app, resources={r"/*": {"origins": "*"}})

# Inicializar base de datos SQLite
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

@app.route('/consultar', methods=['POST'])
def consultar():
    data = request.get_json()
    rut = data.get('rut')
    if not rut:
        return jsonify({'error': 'RUT no proporcionado'}), 400

    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, saldo FROM usuarios WHERE rut = ?", (rut,))
        resultado = cursor.fetchone()

    if resultado:
        nombre, saldo = resultado
        return jsonify({'nombre': nombre, 'saldo': saldo}), 200
    else:
        return jsonify({'error': 'RUT no encontrado'}), 404

@app.route('/registrar_impresion', methods=['POST'])
def registrar_impresion():
    data = request.get_json()
    rut = data.get('rut')
    paginas = data.get('paginas')

    if not rut or paginas is None:
        return jsonify({'error': 'Datos incompletos'}), 400

    try:
        paginas = int(paginas)
    except ValueError:
        return jsonify({'error': 'El valor de páginas debe ser un número entero'}), 400

    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT saldo FROM usuarios WHERE rut = ?", (rut,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        saldo_actual = resultado[0]
        if paginas > saldo_actual:
            return jsonify({'error': 'Saldo insuficiente'}), 400

        nuevo_saldo = saldo_actual - paginas
        cursor.execute("UPDATE usuarios SET saldo = ? WHERE rut = ?", (nuevo_saldo, rut))
        conn.commit()

    return jsonify({
        'mensaje': 'Impresión registrada',
        'nuevo_saldo': nuevo_saldo
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
