"""
    Implementa oauth y OpenIDConnect
    el flujo normal para una aplicación cliente web es:
    1 - register_in_flask
    2 - petición al sitio --> @require_login --> auth_code --> callback --> access_token --> petición original

    el flujo normal para una app que exporta una api
    1 - usa solamente ResourceServer
    2 - petición al sitio --> @require_valid_token --> instrospect_token --> peticion original
"""

import os
import logging
import requests
from requests.auth import HTTPBasicAuth
import urllib
from urllib import parse
import json

import uuid
from functools import wraps
import flask
from flask import redirect, url_for


class ClientCredentialsGrant:
    '''
        https://tools.ietf.org/html/rfc6749
        sección 4.4
    '''

    token_url = os.environ['OIDC_HOST'] + '/oauth2/token'

    def __init__(self, client_id, client_secret, verify=True):
        self.verify = verify
        self.client_id = client_id
        self.client_secret = client_secret

    def access_token(self, scopes=[]):
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        data = {
            'client_id': self.client_id,
            'grant_type': 'client_credentials'
        }
        if len(scopes) > 0:
            data['scope'] = ' '.join(scopes)

        # application/x-www-form-urlencoded
        r = requests.post(self.token_url, verify=self.verify, allow_redirects=False, auth=auth, data=data)
        return r

    def get_token(self, r):
        if r.ok:
            return r.json()['access_token']
        return None


class TokenIntrospection:

    introspect_url = os.environ['OIDC_HOST'] + '/oauth2/introspect'

    def __init__(self, client_id, client_secret, realm='', verify=False):
        self.realm = realm
        self.verify = verify
        self.client_id = client_id
        self.client_secret = client_secret

    def require_valid_token(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            '''
                Recupera y chequea el token por validez
            '''
            token = self.bearer_token(flask.request.headers)
            if not token:
                return self.invalid_token()
            tk = self.verify_token(token)
            if not tk:
                return self.invalid_request()
            kwargs['token'] = tk
            return f(*args, **kwargs)

        return decorated_function


    def bearer_token(self, headers):
        if 'Authorization' in headers:
            auth = headers['Authorization'].split(' ')
            if auth[0].lower() == 'bearer':
                return auth[1]
        return None

    def introspect_token(self, token, scopes=[]):
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        data = {
            'token':token
        }
        if len(scopes) > 0:
            data['scope'] = ' '.join(scopes)
        headers = {
            'Accept':'application/json'
        }
        r = requests.post(self.introspect_url, verify=self.verify, allow_redirects=False, auth=auth, headers=headers, data=data)
        if not r.ok:
            return None
        return r.json()

    def verify_token(self, token, scopes=[]):
        tk = self.introspect_token(token)
        logging.debug(tk)
        if not tk or not tk['active']:
            return None
        return tk


    def invalid_request(self):
        return self.require_auth(text='Bad Request', error='invalid_request', status=400)

    def invalid_token(self):
        return self.require_auth(text='Unauthorized', error='invalid_token', status=401)

    def insufficient_scope(self):
        return self.require_auth(text='Forbidden', error='insufficient_scope', status=403)

    def require_auth(self, text='Unauthorized', error=None, status=401, error_description=''):
        headers = None
        if error:
            headers = {
                'WWW-Authenticate': 'Basic realm=\"{}\", error=\"{}\", error_description:\"{}\"'.format(self.realm, error, error_description)
            }
        else:
            headers = {
                'WWW-Authenticate': 'Basic realm=\"{}\"'.format(self.realm)
            }
        return (text, status, headers)


"""
class OIDC:

    oidc_session = os.environ['OIDC_SESSION']
    userinfo_url = os.environ['HYDRA_HOST'] + '/userinfo'
    auth_url = os.environ['HYDRA_HOST'] + '/oauth2/auth'
    token_url = os.environ['HYDRA_HOST'] + '/oauth2/token'

    default_scopes = ['openid', 'profile', 'email', 'address', 'phone', 'offline']
    default_claims = {
        'userinfo': {
            "given_name": {"essential": True},
            "nickname": None,
            "email": {"essential": True},
            "email_verified": {"essential": True},
            "picture": None
        },
        "id_token": {
            "gender": None,
            "birthdate": {"essential": True}
        }
    }

    def __init__(self, client_id, client_secret, redirect_uri, verify=False):
        #self.session = session
        self.verify = verify
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.resource_server = ResourceServer(client_id=client_id, client_secret=client_secret, verify=verify)

    def auth_code(self, state, nonce, scopes=None, claims=None):
        #application/x-www-form-urlencoded
        #auth = HTTPBasicAuth(client_id, client_secret)

        if not scopes:
            scopes = self.default_scopes

        if not claims:
            claims = self.default_claims

        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'state': state,
            'nonce': nonce,
            'claims': claims
        }
        #r = requests.get(url, verify=False, allow_redirects=False, params=params)
        #return r
        return self.auth_url + "?" + urllib.parse.urlencode(params)

    def access_token(self, code):
        #application/x-www-form-urlencoded
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        data = {
            'client_id': self.client_id,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        r = requests.post(self.token_url, verify=self.verify, allow_redirects=False, auth=auth, data=data)
        return r

    def userinfo(self, token):
        headers = {
            'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post(self.userinfo_url, verify=self.verify, allow_redirects=False, headers=headers)
        if not r.ok:
            return None
        return r.json()


    def register_in_flask(self, app, redirect='/oauth2'):
        app.add_url_rule(redirect, 'oidc_callback', self.callback)

    def callback(self):
        '''
            Callback asociado al flujo de autentificación oauth.
            Obtiene y setea el token dentro de la sesión
        '''
        data = flask.session.get(self.oidc_session, None)
        if not data:
            return ('Bad Request', 400)

        redirect_after = data['redirect_after_login']

        error = flask.request.args.get('error', None, str)
        if error:
            error_desc = flask.request.args.get('error_description', '', str)
            return redirect(redirect_after, error=error, error_description=error_desc)

        code = flask.request.args.get('code', None, str)
        state = flask.request.args.get('state', None, str)

        r = self.access_token(code)
        if not r.ok:
            logging.debug(r.text)
            logging.debug(r.status_code)
            logging.debug(r.headers.items())
            return redirect(redirect_after, error=r.status_code, error_description=r.text)

        token = r.json()
        data['token'] = token
        #flask.session[self.oidc_session] = json.dumps(data)
        flask.session[self.oidc_session] = data
        return redirect(redirect_after)

        '''
        logging.debug(token)
        token['access_token']
        token['expires_in']
        token['id_token']
        token['refresh_token']
        token['scope']
        token['token_type']
        '''

    def require_login(self, f):
        '''
            Verifica que exista un token asociado a la sesión en el servidor para el cliente.
            No verifica la validez del token
            El token es seteado en la sesión en el método callback
        '''
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = flask.session.get(self.oidc_session, None)
            if data:
                #data = json.loads(data)
                if 'token' in data:
                    token = data['token']
                    kwargs['token'] = token
                    return f(*args, **kwargs)

            if not data:
                data = {}

            data['redirect_after_login'] = flask.request.path
            flask.session[self.oidc_session] = data
            r = self.auth_code(state=str(uuid.uuid4()), nonce=str(uuid.uuid4()), scopes=['openid', 'profile', 'email', 'address', 'phone', 'offline','hydra.clients'])
            return redirect(r,302)

        return decorated_function
"""
