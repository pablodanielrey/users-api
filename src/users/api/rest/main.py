import logging
logging.getLogger().setLevel(logging.INFO)
import sys
import base64
import hashlib

from flask import Flask, abort, make_response, jsonify, url_for, request, json, send_from_directory, send_file
from users.model import UsersModel
from flask_jsontools import jsonapi
from dateutil import parser


from rest_utils import register_encoder

from . import reset
from users.model import Session

app = Flask(__name__)
app.debug = True
register_encoder(app)
reset.registrarApiReseteoClave(app)

#@app.route('/users/api/v1.0/usuarios/', methods=['OPTIONS'], defaults={'path':None})
#@app.route('/users/api/v1.0/usuarios/<string:path>', methods=['OPTIONS'])
#@app.route('/users/api/v1.0/usuarios/<path:path>', methods=['OPTIONS'])
#@app.route('/users/api/v1.0/usuarios/<uid>/correos/', methods=['OPTIONS'], defaults={'cid':None})
#@app.route('/users/api/v1.0/usuarios/<uid>/correos/<cid>', methods=['OPTIONS'])
#@app.route('/users/api/v1.0/usuarios/<uid>/correos/<cid>/enviar_confirmar', methods=['OPTIONS'])
#@app.route('/users/api/v1.0/usuarios/<uid>/correos/<cid>/confirmar', methods=['OPTIONS'])
#@app.route('/users/api/v1.0/usuarios/<uid>/claves/', methods=['OPTIONS'])
# def options(*args, **kwargs):
#     '''
#         para autorizar el CORS
#         https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS
#     '''
#     o = request.headers.get('Origin')
#     rm = request.headers.get('Access-Control-Request-Method')
#     rh = request.headers.get('Access-Control-Request-Headers')
#
#     r = make_response()
#     r.headers['Access-Control-Allow-Methods'] = 'PUT,POST,GET,HEAD,DELETE'
#     r.headers['Access-Control-Allow-Origin'] = '*'
#     r.headers['Access-Control-Allow-Headers'] = rh
#     r.headers['Access-Control-Max-Age'] = 1
#     import pprint
#     pprint(r.headers)
#     return r

@app.after_request
def cors_after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


import requests

# @app.route('/users/api/v1.0/avatar/<hash>.json', methods=['GET'])
# @jsonapi
def obtener_avatar(hash):
    return UsersModel.obtener_avatar(hash=hash)

# @app.route('/users/api/v1.0/avatar/', methods=['GET'], defaults={'hash':None})
# @app.route('/users/api/v1.0/avatar/<hash>', methods=['GET'])
def obtener_avatar_binario(hash):
    avatar = obtener_avatar(hash)
    r = make_response()
    r.status_code = 200
    r.data = base64.b64decode(avatar['data'])
    r.headers['Content-Type'] = avatar['content-type']
    return r

@app.route('/users/api/v1.0/avatar/<hash>', methods=['PUT','POST'])
@jsonapi
def agregar_avatar(hash):
    f = request.files['file']
    contenido = base64.b64encode(f.read()).decode('utf-8')
    UsersModel.actualizar_avatar(hash, contenido)
    return {'status':'OK','status_code':200}, 200

@app.route('/users/api/v1.0/usuarios/<uid>/avatar/', methods=['PUT','POST'])
@jsonapi
def agregar_avatar_por_usuario(uid):
    h = hashlib.md5(uid.encode()).hexdigest()
    return agregar_avatar(h)

@app.route('/users/api/v1.0/usuarios/<uid>/avatar/.json', methods=['GET'])
@jsonapi
def obtener_avatar_por_usuario(uid):
    h = hashlib.md5(uid.encode()).hexdigest()
    return obtener_avatar(h)

@app.route('/users/api/v1.0/usuarios/<uid>/avatar/', methods=['GET'])
def obtener_avatar_binario_por_usuario(uid):
    h = hashlib.md5(uid.encode()).hexdigest()
    return obtener_avatar_binario(h)


@app.route('/users/api/v1.0/auth', methods=['POST'])
@jsonapi
def auth():
    data = json.loads(request.data)
    usuario = data['usuario']
    clave = data['clave']
    s = Session()
    try:
        return UsersModel.login(s, usuario, clave)
    finally:
        s.close()


@app.route('/users/api/v1.0/usuarios', methods=['GET'], defaults={'uid':None})
@app.route('/users/api/v1.0/usuarios/', methods=['GET'], defaults={'uid':None})
@app.route('/users/api/v1.0/usuarios/<uid>', methods=['GET'])
@jsonapi
def usuarios(uid):
    search = request.args.get('q', None)
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    mostrarClave = request.args.get('c',False,bool)

    session = Session()
    try:
        if uid:
            us = UsersModel.usuario(session=session, uid=uid, retornarClave=mostrarClave)
            return us

        else:
            fecha_str = request.args.get('f', None)
            fecha = parser.parse(fecha_str) if fecha_str else None
            return UsersModel.usuarios(session=session, search=search, retornarClave=mostrarClave, offset=offset, limit=limit, fecha=fecha)

    finally:
        session.close()

@app.route('/users/api/v1.0/usuarios/<uid>', methods=['PUT','POST'])
@jsonapi
def actualizar_usuario(uid):
    datos = json.loads(request.data)
    session = Session()
    try:
        UsersModel.actualizar_usuario(session, uid, datos)
        session.commit()

    finally:
        session.close()

@app.route('/users/api/v1.0/usuarios/<uid>/claves/', methods=['PUT','POST'])
@jsonapi
def crear_clave(uid):
    data = json.loads(request.data)
    if 'clave' not in data:
        abort(400)

    session = Session()
    try:
        r = UsersModel.cambiar_clave(session, uid, data['clave'])
        session.commit()
        return r
    finally:
        session.close()

@app.route('/users/api/v1.0/generar_clave/<uid>', methods=['GET'])
@jsonapi
def generar_clave(uid):
    session = Session()
    try:
        r = UsersModel.generar_clave(session, uid)
        session.commit()
        return {'uid':uid,'clave:': r}
    finally:
        session.close()


'''
    para los chequeos de precondiciones
'''

@app.route('/users/api/v1.0/usuarios/<uid>/precondiciones', methods=['GET'])
@jsonapi
def precondiciones(uid):
    precondiciones = {}

    session = Session()
    try:
        precondiciones['clave'] = {'debe_cambiarla':False}
        claves = UsersModel.claves(session, uid)
        for c in claves:
            if c.debe_cambiarla:
                precondiciones['clave']['debe_cambiarla'] = True
                break

        precondiciones['correos'] = {'tiene_alternativo':False}
        correos = UsersModel.correos(session, usuario=uid)
        for c in correos:
            if 'econo.unlp.edu.ar' not in c.email and c.confirmado and c.fecha_confirmado and not c.eliminado:
                precondiciones['correos']['tiene_alternativo'] = True
                break
    finally:
        session.close()

    return precondiciones

"""
@app.route('/users/api/v1.0/usuarios/<uid>/claves', methods=['GET'])
@app.route('/users/api/v1.0/usuarios/<uid>/claves/', methods=['GET'])
@jsonapi
def obtener_claves(uid):
    session = Session()
    try:
        return UsersModel.claves(session, uid)
    finally:
        session.close()
"""

"""
@app.route('/users/api/v1.0/claves/', methods=['GET'], defaults={'cid':None})
@app.route('/users/api/v1.0/claves/<cid>', methods=['GET'])
@jsonapi
def claves(cid):
    session = Session()
    try:
        return UsersModel.claves(session=session, cid=cid)
    finally:
        session.close()
"""

@app.route('/users/api/v1.0/usuarios/<uid>/correos', methods=['GET'], defaults={'cid':None})
@app.route('/users/api/v1.0/usuarios/<uid>/correos/', methods=['GET'], defaults={'cid':None})
@app.route('/users/api/v1.0/usuarios/<uid>/correos/<cid>', methods=['GET'])
@jsonapi
def correos_de_usuario(uid, cid):
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    h = request.args.get('h',False,bool)
    session = Session()
    try:
        return UsersModel.correos(session=session, usuario=uid, historico=h, offset=offset, limit=limit)
    except Exception as e:
        logging.exception(e)
        raise e
    finally:
        session.close()

@app.route('/users/api/v1.0/usuarios/<uid>/correos/', methods=['PUT','POST'])
@jsonapi
def agregar_correo(uid):
    assert uid != None
    datos = json.loads(request.data)
    print(datos)
    session = Session()
    try:
        cid = UsersModel.agregar_correo(session=session, uid=uid, datos=datos)
        session.commit()
        UsersModel.enviar_confirmar_correo(session, cid)
        session.commit()

    except Exception as e:
        logging.exception(e)
        raise e
    finally:
        session.close()

@app.route('/users/api/v1.0/usuarios/<uid>/correos/<cid>', methods=['DELETE'])
@app.route('/users/api/v1.0/correos/<cid>', methods=['DELETE'])
@jsonapi
def eliminar_correo(uid=None, cid=None):
    session = Session()
    try:
        UsersModel.eliminar_correo(session, cid)
        session.commit()
    finally:
        session.close()


@app.route('/users/api/v1.0/usuarios/<uid>/correos/<cid>/enviar_confirmar', methods=['GET'])
@jsonapi
def enviar_confirmar_correo(uid, cid):
    session = Session()
    try:
        UsersModel.enviar_confirmar_correo(session, cid)
        session.commit()
    finally:
        session.close()

@app.route('/users/api/v1.0/usuarios/<uid>/correos/<cid>/confirmar', methods=['PUT','POST'])
@jsonapi
def confirmar_correo(uid, cid):
    assert cid is not None
    code = json.loads(request.data)['codigo']

    session = Session()
    try:
        UsersModel.confirmar_correo(session=session, cid=cid, code=code)
        session.commit()
    finally:
        session.close()

@app.route('/users/api/v1.0/correos/', methods=['GET'], defaults={'cid':None})
@app.route('/users/api/v1.0/correos/<cid>', methods=['GET'])
@jsonapi
def correos(cid):
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    h = request.args.get('h',False,bool)
    session = Session()
    try:
        return UsersModel.correos(session=session, historico=h, offset=offset, limit=limit)
    finally:
        session.close()


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/rutas', methods=['GET'])
@jsonapi
def rutas():
    links = []
    for rule in app.url_map.iter_rules():
        url = url_for(rule.endpoint, **(rule.defaults or {}))
        links.append(url)
    return links



def main():
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    main()
