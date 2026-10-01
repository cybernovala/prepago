import os
from datetime import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB = os.environ.get("MONGO_DB", "prepago")

cliente_mongo = MongoClient(MONGO_URI)
db = cliente_mongo[MONGO_DB]
usuarios = db["usuarios"]
historial = db["historial"]

@app.route('/consultar', methods=['POST', 'OPTIONS'])
def consultar():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    data = request.get_json()
    rut = data.get('rut')
    if not rut:
        return _corsify_response(jsonify({'error': 'RUT no proporcionado'}), 400)

    try:
        reg = usuarios.find_one({'rut': rut})
        if not reg:
            return _corsify_response(jsonify({'error': 'RUT no encontrado, asegurate de ingresar el formato 12345678-9, o debes dirigirte a Cybernova en colo colo 512, para realizar una primera recarga y ser registrado(a)'}), 404)

        hist = list(historial.find({'rut': rut}).sort('fecha', -1))
        historial_data = []
        for h in hist:
            fecha = h.get('fecha')
            if isinstance(fecha, datetime):
                fecha_iso = fecha.isoformat()
            elif fecha is not None:
                fecha_iso = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
            else:
                fecha_iso = None
            historial_data.append({'tipo': h.get('tipo'), 'cantidad': h.get('cantidad'), 'fecha': fecha_iso})

        return _corsify_response(jsonify({'nombre': reg['nombre'], 'saldo': reg['saldo_paginas'], 'historial': historial_data}))
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
        reg = usuarios.find_one({'rut': rut})
        if not reg:
            return _corsify_response(jsonify({'error': 'Usuario no encontrado'}), 404)

        saldo = reg['saldo_paginas']
        if paginas > saldo:
            return _corsify_response(jsonify({'error': 'Saldo insuficiente'}), 400)

        nuevo_saldo = saldo - paginas
        usuarios.update_one({'_id': reg['_id']}, {'$set': {'saldo_paginas': nuevo_saldo}})
        historial.insert_one({'rut': rut, 'tipo': 'impresion', 'cantidad': paginas, 'fecha': datetime.now()})
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
        reg = usuarios.find_one({'rut': rut})
        if reg:
            nuevo_saldo = reg['saldo_paginas'] + paginas
            usuarios.update_one({'_id': reg['_id']}, {'$set': {'saldo_paginas': nuevo_saldo}})
        else:
            nuevo_saldo = paginas
            usuarios.insert_one({'nombre': nombre, 'rut': rut, 'saldo_paginas': paginas})

        historial.insert_one({'rut': rut, 'tipo': 'recarga', 'cantidad': paginas, 'fecha': datetime.now()})
        return _corsify_response(jsonify({'mensaje': f'Saldo cargado exitosamente para {nombre}', 'nuevo_saldo': nuevo_saldo}))
    except Exception as e:
        return _corsify_response(jsonify({'error': str(e)}), 500)

@app.route('/get_usuarios', methods=['GET'])
def get_usuarios():
    try:
        rows = usuarios.find({}, {'_id': 0, 'nombre': 1, 'rut': 1, 'saldo_paginas': 1})
        lista = [{'nombre': r.get('nombre'), 'rut': r.get('rut'), 'saldo': r.get('saldo_paginas')} for r in rows]
        return _corsify_response(jsonify({'usuarios': lista}))
    except Exception as e:
        return _corsify_response(jsonify({'error': str(e)}), 500)

# Funciones CORS para manejar OPTIONS y cabeceras

def _build_cors_preflight_response():
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