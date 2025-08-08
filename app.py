# app.py  (ARCHIVO COMPLETO)
import os
from datetime import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

# ---------- CONFIG ----------
# Usa DATABASE_URL si está definido (Neon), si no caerá a sqlite local (dev)
DB_ENV = os.environ.get('DATABASE_URL')
if DB_ENV:
    DATABASE_URL = DB_ENV
else:
    BASE_DIR = os.path.dirname(__file__)
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'usuarios.db')}"

# Para SQLite necesitamos un argumento adicional
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()

# ---------- MODELOS ----------
class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    rut = Column(String, unique=True, nullable=False, index=True)
    saldo = Column(Integer, default=200)

class Historial(Base):
    __tablename__ = 'historial'
    id = Column(Integer, primary_key=True, index=True)
    rut = Column(String, nullable=False, index=True)
    tipo = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha = Column(String, nullable=False)  # ISO string

# Crea tablas si no existen
Base.metadata.create_all(bind=engine)

# ---------- APP ----------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def json_response(payload, status=200):
    resp = make_response(jsonify(payload), status)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

# ---------- RUTAS ----------
@app.route('/consultar', methods=['POST', 'OPTIONS'])
def consultar():
    if request.method == 'OPTIONS':
        return json_response({}, 204)
    data = request.get_json() or {}
    rut = data.get('rut')
    if not rut:
        return json_response({'error': 'RUT no proporcionado'}, 400)

    with SessionLocal() as db:
        usuario = db.query(Usuario).filter(Usuario.rut == rut).first()
        if not usuario:
            return json_response({'error': 'RUT no encontrado'}, 404)

        historial_rows = db.query(Historial).filter(Historial.rut == rut).order_by(Historial.fecha.desc()).all()
        historial_data = [{'tipo': h.tipo, 'cantidad': h.cantidad, 'fecha': h.fecha} for h in historial_rows]

        return json_response({'nombre': usuario.nombre, 'saldo': usuario.saldo, 'historial': historial_data})

@app.route('/registrar_impresion', methods=['POST', 'OPTIONS'])
def registrar_impresion():
    if request.method == 'OPTIONS':
        return json_response({}, 204)
    data = request.get_json() or {}
    rut = data.get('rut')
    paginas = data.get('paginas')
    if not rut or paginas is None:
        return json_response({'error': 'Datos incompletos'}, 400)

    try:
        paginas = int(paginas)
    except (ValueError, TypeError):
        return json_response({'error': 'Páginas debe ser un número'}, 400)
    if paginas <= 0:
        return json_response({'error': 'Páginas debe ser mayor que 0'}, 400)

    with SessionLocal() as db:
        usuario = db.query(Usuario).filter(Usuario.rut == rut).first()
        if not usuario:
            return json_response({'error': 'Usuario no encontrado'}, 404)
        if paginas > usuario.saldo:
            return json_response({'error': 'Saldo insuficiente'}, 400)

        usuario.saldo = usuario.saldo - paginas
        h = Historial(rut=rut, tipo='impresion', cantidad=paginas, fecha=datetime.utcnow().isoformat())
        db.add(h)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return json_response({'mensaje': 'Impresión registrada', 'nuevo_saldo': usuario.saldo})

@app.route('/cargar_usuario', methods=['POST', 'OPTIONS'])
def cargar_usuario():
    if request.method == 'OPTIONS':
        return json_response({}, 204)
    data = request.get_json() or {}
    nombre = data.get('nombre')
    rut = data.get('rut')
    paginas = data.get('paginas')
    if not all([nombre, rut, paginas is not None]):
        return json_response({'error': 'Faltan datos'}, 400)
    try:
        paginas = int(paginas)
    except (ValueError, TypeError):
        return json_response({'error': 'Paginas debe ser entero'}, 400)
    if paginas <= 0:
        return json_response({'error': 'Paginas debe ser mayor que 0'}, 400)

    with SessionLocal() as db:
        usuario = db.query(Usuario).filter(Usuario.rut == rut).first()
        if usuario:
            usuario.saldo = usuario.saldo + paginas
            mensaje = f'Saldo actualizado para {usuario.nombre}'
        else:
            usuario = Usuario(nombre=nombre, rut=rut, saldo=paginas)
            db.add(usuario)
            mensaje = f'Saldo cargado exitosamente para {nombre}'
        h = Historial(rut=rut, tipo='recarga', cantidad=paginas, fecha=datetime.utcnow().isoformat())
        db.add(h)
        db.commit()
        return json_response({'mensaje': mensaje})

@app.route('/get_usuarios', methods=['GET'])
def get_usuarios():
    with SessionLocal() as db:
        users = db.query(Usuario).all()
        usuarios = [{'nombre': u.nombre, 'rut': u.rut, 'saldo': u.saldo} for u in users]
    return json_response({'usuarios': usuarios})

# ---------- RUN ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
