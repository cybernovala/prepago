from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            rut TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            paginas INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT,
            fecha TEXT,
            cambio INTEGER,
            descripcion TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return "API Prepago funcionando"

@app.route("/saldo/<rut>")
def saldo(rut):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE rut = ?", (rut,)).fetchone()
    conn.close()
    if user:
        return jsonify({"nombre": user["nombre"], "paginas": user["paginas"]})
    return jsonify({"error": "Usuario no encontrado"}), 404

@app.route("/admin/recargar", methods=["POST"])
def recargar():
    data = request.get_json()
    rut = data["rut"]
    nombre = data["nombre"]
    paginas = int(data["paginas"])
    descripcion = data.get("descripcion", "Recarga")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE rut = ?", (rut,)).fetchone()
    if user:
        nuevas_paginas = user["paginas"] + paginas
        conn.execute("UPDATE usuarios SET paginas = ? WHERE rut = ?", (nuevas_paginas, rut))
    else:
        conn.execute("INSERT INTO usuarios (rut, nombre, paginas) VALUES (?, ?, ?)", (rut, nombre, paginas))

    conn.execute("INSERT INTO historial (rut, fecha, cambio, descripcion) VALUES (?, ?, ?, ?)",
                 (rut, datetime.now().strftime("%Y-%m-%d %H:%M"), paginas, descripcion))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Recarga aplicada correctamente"})

@app.route("/admin/descontar", methods=["POST"])
def descontar():
    data = request.get_json()
    rut = data["rut"]
    paginas = int(data["paginas"])
    descripcion = data.get("descripcion", "Descuento por impresión")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE rut = ?", (rut,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    nuevas_paginas = max(0, user["paginas"] - paginas)
    conn.execute("UPDATE usuarios SET paginas = ? WHERE rut = ?", (nuevas_paginas, rut))
    conn.execute("INSERT INTO historial (rut, fecha, cambio, descripcion) VALUES (?, ?, ?, ?)",
                 (rut, datetime.now().strftime("%Y-%m-%d %H:%M"), -paginas, descripcion))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Descuento aplicado correctamente"})

@app.route("/admin/historial/<rut>")
def historial(rut):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM historial WHERE rut = ? ORDER BY fecha DESC", (rut,)).fetchall()
    conn.close()
    historial = [{"fecha": r["fecha"], "cambio": r["cambio"], "descripcion": r["descripcion"]} for r in rows]
    return jsonify(historial)

# ESTA LÍNEA ES CLAVE PARA QUE FUNCIONE EN RENDER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
