from flask import Flask, request, jsonify, render_template, redirect, url_for
from tinydb import TinyDB, Query
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

db = TinyDB('db_prepago.json')
Usuario = Query()

PAGINAS_POR_5000 = 200
PRECIO_POR_PAGINA = 25

def calcular_paginas_restantes(rut):
    recargas = db.search((Usuario.rut == rut) & (Usuario.tipo == 'recarga'))
    impresiones = db.search((Usuario.rut == rut) & (Usuario.tipo == 'impresion'))

    total_cargado = sum(r['monto'] for r in recargas)
    total_paginas_cargadas = (total_cargado // 5000) * PAGINAS_POR_5000
    total_paginas_usadas = sum(i['paginas'] for i in impresiones)

    return total_paginas_cargadas - total_paginas_usadas

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/consultar_usuario', methods=['POST'])
def consultar_usuario():
    data = request.get_json()
    rut = data.get('rut')
    if not rut:
        return jsonify({'success': False, 'error': 'Falta RUT'})

    recargas = db.search((Usuario.rut == rut) & (Usuario.tipo == 'recarga'))
    if not recargas:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'})

    nombre = recargas[0]['nombre']
    paginas_restantes = calcular_paginas_restantes(rut)

    return jsonify({
        'success': True,
        'nombre': nombre,
        'paginas_restantes': paginas_restantes
    })

@app.route('/admin')
def admin_menu():
    return render_template('menu_admin.html')

@app.route('/admin/recarga', methods=['POST'])
def registrar_recarga():
    nombre = request.form.get('nombre', '').strip().upper()
    rut = request.form.get('rut', '').strip()
    monto = int(request.form.get('monto', '0'))

    if not nombre or not rut or monto <= 0:
        return "Datos incompletos o inválidos", 400

    db.insert({
        'tipo': 'recarga',
        'nombre': nombre,
        'rut': rut,
        'monto': monto
    })

    return redirect(url_for('admin_menu'))

@app.route('/admin/imprimir', methods=['GET', 'POST'])
def admin_imprimir():
    if request.method == 'GET':
        return render_template('imprime_admin.html', usuario=None)

    # POST
    rut = request.form.get('rut', '').strip()
    if not rut:
        return "RUT requerido", 400

    # Si viene solo el RUT para buscar:
    if 'cantidad_paginas' not in request.form:
        recargas = db.search((Usuario.rut == rut) & (Usuario.tipo == 'recarga'))
        if not recargas:
            return render_template('imprime_admin.html', usuario=None, error="Usuario no encontrado")

        nombre = recargas[0]['nombre']
        paginas_restantes = calcular_paginas_restantes(rut)
        usuario = {
            'nombre': nombre,
            'rut': rut,
            'paginas_restantes': paginas_restantes
        }
        return render_template('imprime_admin.html', usuario=usuario)

    # Confirmar impresión y descontar páginas
    cantidad_paginas = int(request.form.get('cantidad_paginas', '0'))
    concepto = request.form.get('concepto', '').strip()

    if cantidad_paginas <= 0 or not concepto:
        return "Datos inválidos", 400

    paginas_restantes = calcular_paginas_restantes(rut)
    if cantidad_paginas > paginas_restantes:
        return render_template('imprime_admin.html', usuario=None, error="Saldo insuficiente")

    db.insert({
        'tipo': 'impresion',
        'rut': rut,
        'paginas': cantidad_paginas,
        'concepto': concepto
    })

    return redirect(url_for('admin_imprimir'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

@app.route("/ver_base")
def ver_base():
    return jsonify(db.all())


