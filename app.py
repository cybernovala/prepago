from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# Crear la base de datos si no existe
def init_db():
    with sqlite3.connect("usuarios.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            rut TEXT NOT NULL UNIQUE,
                            saldo INTEGER DEFAULT 200
                        )''')
init_db()

@app.route('/')
def index():
    return render_template('index.html')

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
        return jsonify({'nombre': nombre, 'saldo': saldo})
    else:
        return jsonify({'error': 'RUT no encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
