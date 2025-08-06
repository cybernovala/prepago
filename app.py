from flask import Flask, request, jsonify, render_template
import json
import os

app = Flask(__name__)

REGISTROS_PATH = "registros.json"

# Cargar o crear base de datos
if not os.path.exists(REGISTROS_PATH):
    with open(REGISTROS_PATH, "w") as f:
        json.dump([], f)

def cargar_registros():
    with open(REGISTROS_PATH, "r") as f:
        return json.load(f)

def guardar_registros(registros):
    with open(REGISTROS_PATH, "w") as f:
        json.dump(registros, f, indent=2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/consultar", methods=["POST"])
def consultar():
    data = request.get_json()
    rut = data.get("rut")
    registros = cargar_registros()
    for registro in registros:
        if registro["rut"] == rut:
            return jsonify(registro)
    return jsonify({"error": "RUT no encontrado"}), 404

@app.route("/actualizar", methods=["POST"])
def actualizar():
    data = request.get_json()
    rut = data.get("rut")
    paginas_usadas = data.get("paginas_usadas")
    registros = cargar_registros()
    for registro in registros:
        if registro["rut"] == rut:
            registro["paginas_restantes"] -= paginas_usadas
            guardar_registros(registros)
            return jsonify({"mensaje": "Actualizado correctamente"})
    return jsonify({"error": "RUT no encontrado"}), 404
