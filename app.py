from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    with sqlite3.connect("usuarios.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            rut TEXT NOT NULL UNIQUE,
                            saldo INTEGER DEFAULT 0
                        )''')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cargar_usuario', methods=['POST'])
def cargar_usuario():
    data = request.get_json()
    nombre = data.get('nombre')
    rut = data.get('rut')
    paginas = data.get('paginas')

    if not nombre or not rut or paginas is None:
        return jsonify({'error': 'Faltan datos'}), 400

    with sqlite3.connect("usuarios.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE rut = ?", (rut,))
        existe = cursor.fetchone()

        if existe:
            cursor.execute("UPDATE usuarios SET saldo = saldo + ? WHERE rut = ?", (paginas, rut))
            mensaje = "Saldo actualizado correctamente"
        else:
            cursor.execute("INSERT INTO usuarios (nombre, rut, saldo) VALUES (?, ?, ?)", (nombre, rut, paginas))
            mensaje = "Usuario creado y saldo cargado"

        conn.commit()

    return jsonify({'mensaje': mensaje})

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
