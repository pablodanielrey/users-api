import logging
logging.getLogger().setLevel(logging.DEBUG)

from flask import Flask, abort, make_response, jsonify, url_for, request, json, send_from_directory
from users.model import ResetClaveModel
from users.model.exceptions import *
from flask_jsontools import jsonapi

from users.model import Session

def _obtener_token_de_authorization():
    token = None
    auth = request.authorization
    logging.debug(auth)
    if auth is None and 'Authorization' in request.headers:
        try:
            header = request.headers['Authorization']
            auth_type, tk = header.split(None,1)
            token = tk
        except ValueError:
            pass

    if not token and auth:
        token = auth.username

    return token


def registrarApiReseteoClave(app):

    @app.route('/users/api/v1.0/reset/obtener_token', methods=['OPTIONS'])
    @app.route('/users/api/v1.0/reset/obtener_usuario/<dni>', methods=['OPTIONS'])
    @app.route('/users/api/v1.0/reset/enviar_codigo', methods=['OPTIONS'])
    @app.route('/users/api/v1.0/reset/verificar_codigo', methods=['OPTIONS'])
    @app.route('/users/api/v1.0/reset/cambiar_clave', methods=['OPTIONS'])
    def reset_options(*args, **kargs):
        '''
            para autorizar el CORS
            https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS
        '''
        o = request.headers.get('Origin')
        rm = request.headers.get('Access-Control-Request-Method')
        rh = request.headers.get('Access-Control-Request-Headers')

        r = make_response()
        r.headers['Access-Control-Allow-Methods'] = 'PUT,POST,GET,HEAD,DELETE'
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Headers'] = rh
        r.headers['Access-Control-Max-Age'] = 1
        return r

    """
    @app.route('/users/api/v1.0/reset/token/<int:encoder>', methods=['GET'], defaults={'token':None})
    @app.route('/users/api/v1.0/reset/token/<int:encoder>/<token>', methods=['GET'])
    @jsonapi
    def reset_test_decode_token(encoder,token):
        if token:
            return ResetClaveModel._test_decode_token(encoder,token)
        else:
            return ResetClaveModel._test_encode_token(encoder)
    """

    @app.route('/users/api/v1.0/reset/verificaciones', methods=['GET'])
    @jsonapi
    def reset_obtener_verificaciones_de_codigo():
        solo_pendientes = request.args.get('p', False, bool)
        limit = request.args.get('limit', None, int)
        offset = request.args.get('offset', None, int)
        return ResetClaveModel.verificaciones(solo_pendientes=solo_pendientes, limit=limit, offset=offset)

    @app.errorhandler(UsersError)
    def reset_retorar_error(error):
        return jsonify(error), error.status_code

    @app.errorhandler(ResetClaveError)
    def reset_retorar_error(error):
        return jsonify(error), error.status_code

    @app.route('/users/api/v1.0/reset/obtener_token', methods=['GET'])
    @jsonapi
    def reset_obtener_token():
        return ResetClaveModel.obtener_token()

    @app.route('/users/api/v1.0/reset/obtener_usuario/<dni>', methods=['GET'])
    @jsonapi
    def reset_obtener_usuario(dni):
        token = _obtener_token_de_authorization()
        if not token:
            abort(403)
        session = Session()
        try:
            return ResetClaveModel.obtener_usuario(session, token, dni)
            session.commit()

        except ResetClaveError as e:
            session.commit()
            raise e

        finally:
            session.close()

    @app.route('/users/api/v1.0/reset/enviar_codigo', methods=['POST'])
    @jsonapi
    def reset_enviar_codigo():
        token = _obtener_token_de_authorization()
        if not token:
            abort(403)
        return ResetClaveModel.enviar_codigo(token)

    @app.route('/users/api/v1.0/reset/verificar_codigo', methods=['POST'])
    @jsonapi
    def reset_verificar_codigo():
        token = _obtener_token_de_authorization()
        if not token:
            abort(403)
        datos = json.loads(request.data)
        if not 'codigo' in datos:
            abort(400)
        return ResetClaveModel.verificar_codigo(token, datos['codigo'])


    @app.route('/users/api/v1.0/reset/cambiar_clave', methods=['POST'])
    @jsonapi
    def reset_cambiar_clave():
        token = _obtener_token_de_authorization()
        if not token:
            abort(403)
        datos = json.loads(request.data)
        if not 'clave' in datos:
            abort(400)

        session = Session()
        try:
            r = ResetClaveModel.cambiar_clave(session, token, datos['clave'])
            session.commit()
            return r
        finally:
            session.close()
