from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # Permite CORS para todas las rutas y orígenes

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cargar_usuario', methods=['POST'])
def cargar_usuario():
    data = request.get_json()
    nombre = data.get('nombre')
    rut = data.get('rut')
    paginas = data.get('paginas')

    if not all([nombre, rut, paginas]):
        return jsonify({'error': 'Faltan datos'}), 400

    try:
        with sqlite3.connect("usuarios.db") as conn:
            cursor = conn.cursor()
            # Verificar si usuario existe
            cursor.execute("SELECT saldo FROM usuarios WHERE rut = ?", (rut,))
            res = cursor.fetchone()

            if res:
                # Actualizar saldo sumando paginas
                nuevo_saldo = res[0] + paginas
                cursor.execute("UPDATE usuarios SET saldo = ? WHERE rut = ?", (nuevo_saldo, rut))
            else:
                # Insertar nuevo usuario
                cursor.execute("INSERT INTO usuarios (nombre, rut, saldo) VALUES (?, ?, ?)",
                               (nombre, rut, paginas))
            conn.commit()
        return jsonify({'mensaje': f'Saldo cargado exitosamente para {nombre}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
