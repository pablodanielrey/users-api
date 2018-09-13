import logging
logging.getLogger().setLevel(logging.INFO)
import sys
import base64
import hashlib
import os

from flask import Flask, abort, make_response, jsonify, url_for, request, json, send_from_directory, send_file
from users.model import UsersModel
from flask_jsontools import jsonapi
from dateutil import parser
import datetime

from rest_utils import register_encoder

from . import reset
from users.model import obtener_session

VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))

import oidc
from oidc.oidc import TokenIntrospection
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']
rs = TokenIntrospection(client_id, client_secret, verify=VERIFY_SSL)

from warden.sdk.warden import Warden
warden_url = os.environ['WARDEN_API_URL']
warden = Warden(warden_url, client_id, client_secret, verify=VERIFY_SSL)

API_BASE=os.environ['API_BASE']

app = Flask(__name__)
app.debug = True
register_encoder(app)
reset.registrarApiReseteoClave(app)

@app.after_request
def cors_after_request(response):
    if not response.headers.get('Access-Control-Allow-Origin',None):
        response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


import requests

# @app.route(API_BASE + '/avatar/<hash>.json', methods=['GET'])
# @jsonapi
def obtener_avatar(hash):
    return UsersModel.obtener_avatar(hash=hash)

# @app.route(API_BASE + '/avatar/', methods=['GET'], defaults={'hash':None})
# @app.route(API_BASE + '/avatar/<hash>', methods=['GET'])
def obtener_avatar_binario(hash):
    avatar = obtener_avatar(hash)
    r = make_response()
    r.status_code = 200
    r.data = base64.b64decode(avatar['data'])
    r.headers['Content-Type'] = avatar['content-type']
    return r

@app.route(API_BASE + '/avatar/<hash>', methods=['PUT','POST'])
@rs.require_valid_token
@jsonapi
def agregar_avatar(hash, token=None):
    f = request.files['file']
    contenido = base64.b64encode(f.read()).decode('utf-8')
    UsersModel.actualizar_avatar(hash, contenido)
    return {'status':'OK','status_code':200}, 200

@app.route(API_BASE + '/usuarios/<uid>/avatar/', methods=['PUT','POST'])
@rs.require_valid_token
@jsonapi
def agregar_avatar_por_usuario(uid, token=None):
    h = hashlib.md5(uid.encode()).hexdigest()
    return agregar_avatar(h)

@app.route(API_BASE + '/usuarios/<uid>/avatar/.json', methods=['GET'])
@rs.require_valid_token
@jsonapi
def obtener_avatar_por_usuario(uid, token=None):
    h = hashlib.md5(uid.encode()).hexdigest()
    return obtener_avatar(h)

@app.route(API_BASE + '/usuarios/<uid>/avatar/', methods=['GET'])
def obtener_avatar_binario_por_usuario(uid, token=None):
    h = hashlib.md5(uid.encode()).hexdigest()
    return obtener_avatar_binario(h)


@app.route(API_BASE + '/auth', methods=['POST'])
@rs.require_valid_token
@jsonapi
def auth(token=None):
    logging.debug('Token RECIBIDO : {}'.format(token))

    '''
        chequeo que solo sea la app de consent la que pueda llamar a este método
        client_id = consent
    '''
    if token['client_id'] != 'consent':
        return {'error':'No permitido', 'status_code':403}, 403

    data = json.loads(request.data)
    usuario = data['usuario']
    clave = data['clave']
    with obtener_session() as session:
        return UsersModel.login(session, usuario, clave)

@app.route(API_BASE + '/usuarios', methods=['GET'], defaults={'uid':None})
@app.route(API_BASE + '/usuarios/', methods=['GET'], defaults={'uid':None})
@app.route(API_BASE + '/usuarios/<uid>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def usuarios(uid, token=None):
    search = request.args.get('q', None)
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)

    admin = False
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if prof['profile']:
        mostrarClave = request.args.get('c',False,bool)
        admin = True
    else:
        prof = warden.has_all_profiles(token, ['users-admin'])
        admin = prof['profile']

    if not admin:
        auid = token['sub']
        if auid != uid:
            return ('no tiene los permisos suficientes', 403)

    with obtener_session() as session:
        if uid:
            us = UsersModel.usuario(session=session, uid=uid, retornarClave=mostrarClave)
            return us
        else:
            fecha_str = request.args.get('f', None)
            fecha = parser.parse(fecha_str) if fecha_str else None
            return UsersModel.usuarios(session=session, search=search, retornarClave=mostrarClave, offset=offset, limit=limit, fecha=fecha)

@app.route(API_BASE + '/usuarios', methods=['PUT'])
@rs.require_valid_token
@jsonapi
def crear_usuario(token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    usuario = request.get_json()
    logging.debug(usuario)
    with obtener_session() as session:
        uid = UsersModel.crear_usuario(session, usuario)
        session.commit()
        return uid

@app.route(API_BASE + '/usuarios/<uid>', methods=['PUT','POST'])
@rs.require_valid_token
@jsonapi
def actualizar_usuario(uid, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    datos = json.loads(request.data)
    with obtener_session() as session:
        UsersModel.actualizar_usuario(session, uid, datos)
        session.commit()

'''
    para los chequeos de precondiciones
'''

@app.route(API_BASE + '/usuarios/<uid>/precondiciones', methods=['GET'])
@rs.require_valid_token
@jsonapi
def precondiciones(uid, token=None):
    precondiciones = {}
    with obtener_session() as session:
        precondiciones['clave'] = {'debe_cambiarla':False}
        claves = UsersModel.claves(session, uid)
        for c in claves:
            if c.debe_cambiarla:
                precondiciones['clave']['debe_cambiarla'] = True
                break

        precondiciones['correos'] = {'tiene_alternativo':False}
        correos = UsersModel.correos(session, usuario=uid)
        for c in correos:
            if 'econo.unlp.edu.ar' not in c.email and c.confirmado and not c.eliminado:
                precondiciones['correos']['tiene_alternativo'] = True
                break
    return precondiciones

@app.route(API_BASE + '/usuarios/<uid>/correos', methods=['GET'], defaults={'cid':None})
@app.route(API_BASE + '/usuarios/<uid>/correos/', methods=['GET'], defaults={'cid':None})
@app.route(API_BASE + '/usuarios/<uid>/correos/<cid>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def correos_de_usuario(uid, cid, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    h = request.args.get('h',False,bool)
    with obtener_session() as session:
        return UsersModel.correos(session=session, usuario=uid, historico=h, offset=offset, limit=limit)

@app.route(API_BASE + '/usuarios/<uid>/correo', methods=['PUT','POST'])
@rs.require_valid_token
@jsonapi
def agregar_correo_institucional(uid, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    assert uid != None
    datos = json.loads(request.data)
    assert datos['correo'] != None
    with obtener_session() as session:
        if not UsersModel.existe(session=session, usuario=uid):
            raise Exception('Usuario no existente')

        mail = UsersModel.obtener_correo_por_cuenta(session=session, cuenta=datos['correo'])
        if not mail:
            mail = UsersModel.agregar_correo_institucional(session=session, uid=uid, datos={'email':datos['correo']})
            session.commit()
        else:
            mail.confirmado = datetime.datetime.now()
            session.commit()
        return mail.id

@app.route(API_BASE + '/usuarios/<uid>/correos/', methods=['PUT','POST'])
@rs.require_valid_token
@jsonapi
def agregar_correo(uid, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    assert uid != None
    datos = json.loads(request.data)
    print(datos)
    with obtener_session() as session:
        cid = UsersModel.agregar_correo(session=session, uid=uid, datos=datos)
        session.commit()
        UsersModel.enviar_confirmar_correo(session, cid)
        session.commit()

@app.route(API_BASE + '/usuarios/<uid>/correos/<cid>', methods=['DELETE'])
@app.route(API_BASE + '/correos/<cid>', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def eliminar_correo(uid=None, cid=None, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    assert uid != None
    assert cid != None
    with obtener_session() as session:
        UsersModel.eliminar_correo(session, cid)
        session.commit()
        return {'id':cid}

@app.route(API_BASE + '/usuarios/<uid>/telefonos/<tid>', methods=['DELETE'])
@app.route(API_BASE + '/telefonos/<tid>', methods=['DELETE'])
@rs.require_valid_token
@jsonapi
def eliminar_telefono(uid=None, tid=None, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']: 
        return ('no tiene los permisos suficientes', 403)

    assert uid != None
    assert tid != None
    with obtener_session() as session:
        UsersModel.eliminar_telefono(session, tid)
        session.commit()
        return {'id':tid}


@app.route(API_BASE + '/usuarios/<uid>/correos/<cid>/enviar_confirmar', methods=['GET'])
@rs.require_valid_token
@jsonapi
def enviar_confirmar_correo(uid, cid, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    with obtener_session() as session:
        UsersModel.enviar_confirmar_correo(session, cid)
        session.commit()

@app.route(API_BASE + '/usuarios/<uid>/correos/<cid>/confirmar', methods=['PUT','POST'])
@rs.require_valid_token
@jsonapi
def confirmar_correo(uid, cid, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    assert cid is not None
    code = json.loads(request.data)['codigo']
    with obtener_session() as session:
        UsersModel.confirmar_correo(session=session, cid=cid, code=code)
        session.commit()

@app.route(API_BASE + '/correos/<cuenta>', methods=['GET'])
@rs.require_valid_token
@jsonapi
def chequear_disponibilidad_cuenta(cuenta, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    with obtener_session() as session:
        correo = UsersModel.obtener_correo_por_cuenta(session=session, cuenta=cuenta)
        if correo:
            return {'existe':True, 'correo': correo}
        else:
            return {'existe':False, 'correo':None}


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


'''
@app.route('/rutas', methods=['GET'])
@jsonapi
def rutas():
    links = []
    for rule in app.url_map.iter_rules():
        url = url_for(rule.endpoint, **(rule.defaults or {}))
        links.append(url)
    return links
'''


def main():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
