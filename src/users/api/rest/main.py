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
from users.model import obtener_session

VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))
OIDC_URL = os.environ['OIDC_URL']
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']


from warden.sdk.warden import Warden
warden_url = os.environ['WARDEN_API_URL']
warden = Warden(OIDC_URL, warden_url, client_id, client_secret, verify=VERIFY_SSL)

API_BASE=os.environ['API_BASE']

app = Flask(__name__)
app.debug = True
register_encoder(app)

DEBUGGING = bool(int(os.environ.get('VSC_DEBUGGING',0)))
def configurar_debugger():
    """
    para debuggear con visual studio code
    """
    if DEBUGGING:
        print('Iniciando Debugger PTVSD')
        import ptvsd
        #secret = os.environ.get('VSC_DEBUG_KEY',None)
        port = int(os.environ.get('VSC_DEBUGGING_PORT', 5678))
        ptvsd.enable_attach(address=('0.0.0.0',port))

configurar_debugger()


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
@warden.require_valid_token
@jsonapi
def agregar_avatar(hash, token=None):
    f = request.files['file']
    contenido = base64.b64encode(f.read()).decode('utf-8')
    UsersModel.actualizar_avatar(hash, contenido)
    return {'status':'OK','status_code':200}, 200

@app.route(API_BASE + '/usuarios/<uid>/avatar/', methods=['PUT','POST'])
@warden.require_valid_token
@jsonapi
def agregar_avatar_por_usuario(uid, token=None):
    h = hashlib.md5(uid.encode()).hexdigest()
    return agregar_avatar(h)

@app.route(API_BASE + '/usuarios/<uid>/avatar/.json', methods=['GET'])
@warden.require_valid_token
@jsonapi
def obtener_avatar_por_usuario(uid, token=None):
    h = hashlib.md5(uid.encode()).hexdigest()
    return obtener_avatar(h)

@app.route(API_BASE + '/usuarios/<uid>/avatar/', methods=['GET'])
def obtener_avatar_binario_por_usuario(uid, token=None):
    h = hashlib.md5(uid.encode()).hexdigest()
    return obtener_avatar_binario(h)

@app.route(API_BASE + '/usuario_por_dni/<dni>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def usuario_por_dni(dni, token=None):
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if not prof or not prof['profile']:
        return ('Insuficient access', 401)

    with obtener_session() as s:
        u = UsersModel.usuario_por_dni(session=s, dni=dni)
        return u

@app.route(API_BASE + '/usuarios/', methods=['GET'], defaults={'uid':None})
@app.route(API_BASE + '/usuarios/<uid>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def usuarios(uid, token=None):

    """
    para poder debuggear el require valid token.
    token = warden._require_valid_token()
    if not token:
        return warden._invalid_token()
    """

    search = request.args.get('q', None)
    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)

    admin = False
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if prof and prof['profile']:
        admin = True
    else:
        prof = warden.has_all_profiles(token, ['users-admin'])
        if prof:
            admin = prof['profile']

    if not admin:
        auid = token['sub']
        if auid != uid:
            return ('no tiene los permisos suficientes', 403)

    with obtener_session() as session:
        if uid:
            us = UsersModel.usuario(session=session, uid=uid)
            return us
        else:
            us = UsersModel.usuarios(session=session, search=search, offset=offset, limit=limit)
            return us

@app.route(API_BASE + '/usuarios', methods=['PUT'])
@warden.require_valid_token
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
@warden.require_valid_token
@jsonapi
def actualizar_usuario(uid, token=None):

    admin = False
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if prof and prof['profile']:
        admin = True
    else:
        prof = warden.has_all_profiles(token, ['users-admin'])
        if prof:
            admin = prof['profile']

    if not admin:
        auid = token['sub']
        if auid != uid:
            return ('no tiene los permisos suficientes', 403)   

    datos = json.loads(request.data)
    with obtener_session() as session:
        UsersModel.actualizar_usuario(session, uid, datos)
        session.commit()
        return uid


@app.route(API_BASE + '/usuarios/<uid>/correos', methods=['GET'], defaults={'cid':None})
@app.route(API_BASE + '/usuarios/<uid>/correos/', methods=['GET'], defaults={'cid':None})
@app.route(API_BASE + '/usuarios/<uid>/correos/<cid>', methods=['GET'])
@warden.require_valid_token
@jsonapi
def correos_de_usuario(uid, cid, token=None):

    admin = False
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if prof and prof['profile']:
        admin = True
    else:
        prof = warden.has_all_profiles(token, ['users-admin'])
        if prof:
            admin = prof['profile']

    if not admin:
        auid = token['sub']
        if auid != uid:
            return ('no tiene los permisos suficientes', 403)        

    offset = request.args.get('offset',None,int)
    limit = request.args.get('limit',None,int)
    h = request.args.get('h',False,bool)
    with obtener_session() as session:
        return UsersModel.correos(session=session, usuario=uid, historico=h, offset=offset, limit=limit)

@app.route(API_BASE + '/usuarios/<uid>/correo_institucional', methods=['PUT','POST'])
@warden.require_valid_token
@jsonapi
def agregar_correo_institucional(uid, token=None):

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    assert uid != None
    datos = json.loads(request.data)
    assert datos['email'] != None
    with obtener_session() as session:
        if not UsersModel.existe(session=session, usuario=uid):
            raise Exception('Usuario no existente')

        mail = UsersModel.obtener_correo_por_cuenta(session=session, cuenta=datos['email'])
        if not mail:
            mail = UsersModel.agregar_correo_institucional(session=session, uid=uid, datos=datos)
            session.commit()
        else:
            mail.confirmado = datetime.datetime.now()
            session.commit()
        return mail.id

@app.route(API_BASE + '/usuarios/<uid>/correos/', methods=['PUT','POST'])
@warden.require_valid_token
@jsonapi
def agregar_correo(uid, token=None):

    admin = False
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if prof and prof['profile']:
        admin = True
    else:
        prof = warden.has_all_profiles(token, ['users-admin'])
        if prof:
            admin = prof['profile']

    if not admin:
        auid = token['sub']
        if auid != uid:
            return ('no tiene los permisos suficientes', 403)

    assert uid != None
    datos = json.loads(request.data)
    with obtener_session() as session:
        cid = UsersModel.agregar_correo(session=session, uid=uid, datos=datos)
        session.commit()
        UsersModel.enviar_confirmar_correo(session, cid)
        session.commit()
        return {'cid':cid}

@app.route(API_BASE + '/usuarios/<uid>/correos/<cid>', methods=['DELETE'])
@app.route(API_BASE + '/correos/<cid>', methods=['DELETE'])
@warden.require_valid_token
@jsonapi
def eliminar_correo(uid=None, cid=None, token=None):

    if not uid:
        uid = token['sub']

    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        if uid != token['sub']:
            return ('no tiene los permisos suficientes', 403)

    assert uid != None
    assert cid != None
    with obtener_session() as session:
        UsersModel.eliminar_correo(session, cid)
        session.commit()
        return {'id':cid}


@app.route(API_BASE + '/usuarios/<uid>/telefonos/<tid>', methods=['DELETE'])
@app.route(API_BASE + '/telefonos/<tid>', methods=['DELETE'])
@warden.require_valid_token
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
@warden.require_valid_token
@jsonapi
def enviar_confirmar_correo(uid, cid, token=None):

    admin = False
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if prof and prof['profile']:
        admin = True
    else:
        prof = warden.has_all_profiles(token, ['users-admin'])
        if prof:
            admin = prof['profile']

    if not admin:
        auid = token['sub']
        if auid != uid:
            return ('no tiene los permisos suficientes', 403)

    with obtener_session() as session:
        UsersModel.enviar_confirmar_correo(session, cid)
        session.commit()

@app.route(API_BASE + '/usuarios/<uid>/correos/<cid>/confirmar', methods=['PUT','POST'])
@warden.require_valid_token
@jsonapi
def confirmar_correo(uid, cid, token=None):

    admin = False
    prof = warden.has_all_profiles(token, ['users-super-admin'])
    if prof and prof['profile']:
        admin = True
    else:
        prof = warden.has_all_profiles(token, ['users-admin'])
        if prof:
            admin = prof['profile']

    if not admin:
        auid = token['sub']
        if auid != uid:
            return ('no tiene los permisos suficientes', 403)

    assert cid is not None
    code = json.loads(request.data)['codigo']
    with obtener_session() as session:
        UsersModel.confirmar_correo(session=session, cid=cid, code=code)
        session.commit()

@app.route(API_BASE + '/correos/<cuenta>', methods=['GET'])
@warden.require_valid_token
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


"""
    //////////////////////////////////////////////////////////
    ///////////////////// SINC GOOGLE ////////////////////////
    //////////////////////////////////////////////////////////
"""

from users.model.google.GoogleModel import GoogleModel

@app.route(API_BASE + '/usuarios/<uid>/sincronizar_google', methods=['GET'])
#@warden.require_valid_token
@jsonapi
def sincronizar_usuario(uid, token=None):

    with obtener_session() as session:
        r = GoogleModel.sincronizar(session, uid)
        return r

@app.route(API_BASE + '/usuarios/sincronizar_google', methods=['GET'])
#@warden.require_valid_token
@jsonapi
def sincronizar_usuarios(token=None):

    with obtener_session() as session:
        r = GoogleModel.sincronizar_dirty(session)
        session.commit()
        return r




"""
    ////////////////////////////////////////////////////////////////
    //////////////////////// PRECONDICIONES ////////////////////////
    ////////////////////////////////////////////////////////////////
"""

@app.route(API_BASE + '/precondiciones', methods=['GET'])
@warden.require_valid_token
@jsonapi
def chequear_precondiciones_usuario(token=None):
    uid = token['sub']
    assert uid is not None
    with obtener_session() as s:
        return UsersModel.precondiciones(s,uid)

@app.route(API_BASE + '/usuarios/<uid>/precondiciones', methods=['GET'])
@warden.require_valid_token
@jsonapi
def chequear_precondiciones_de_usuario(uid, token=None):
    assert uid is not None
    prof = warden.has_one_profile(token, ['users-super-admin', 'users-admin'])
    if not prof['profile']:
        return ('no tiene los permisos suficientes', 403)

    with obtener_session() as s:
        return UsersModel.precondiciones(s,uid)






@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET','POST','PUT','PATCH'])
def catch_all(path):
    return ('no permitido', 401)

if DEBUGGING:
    @app.before_request
    def br():
        logging.info(request)

@app.route(API_BASE + '*', methods=['OPTIONS'])
def options():
    if request.method == 'OPTIONS':
        return 204
    return 204

def cors_after_request(response):
    if not response.headers.get('Access-Control-Allow-Origin',None):
        response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.after_request
def add_header(r):
    r = cors_after_request(r)
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
    app.run(host='0.0.0.0', port=10102, debug=False)

if __name__ == '__main__':
    main()
