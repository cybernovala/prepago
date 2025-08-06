from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    with sqlite3.connect("usuarios.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            rut TEXT NOT NULL UNIQUE,
                            saldo INTEGER DEFAULT 200
                        )''')

def insertar_usuarios_demo():
    usuarios_demo = [
        ("JUAN PÉREZ", "11111111-1", 150),
        ("MARÍA GÓMEZ", "22222222-2", 80)
    ]
    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        for nombre, rut, saldo in usuarios_demo:
            try:
                cursor.execute("INSERT INTO usuarios (nombre, rut, saldo) VALUES (?, ?, ?)", (nombre, rut, saldo))
            except sqlite3.IntegrityError:
                pass
        conn.commit()

init_db()
insertar_usuarios_demo()

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

@app.route('/consulta')
def consulta():
    rut = request.args.get('rut')
    if not rut:
        return jsonify({'error': 'RUT no proporcionado'}), 400

    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, saldo FROM usuarios WHERE rut = ?", (rut,))
        resultado = cursor.fetchone()

    if resultado:
        nombre, saldo = resultado
        return jsonify({'nombre': nombre, 'rut': rut, 'paginas_restantes': saldo})
    else:
        return jsonify({'error': 'RUT no encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
