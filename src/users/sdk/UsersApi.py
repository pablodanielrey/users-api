
from oidc.oidc import ClientCredentialsGrant

class UsersApi:

    def __init__(self, oidc_url, client_id, client_secret, users_api_url, verify=True):
        self.cc = ClientCredentialsGrant(oidc_url, client_id, client_secret, verify)
        self.users_api_url = users_api_url

    def get_token(self):
        r = self.cc.access_token()
        tk = self.cc.get_token(r)
        return tk

    @staticmethod
    def get_auth_headers(tk):
        headers = {
            'Authorization': 'Bearer {}'.format(tk),
            'Accept':'application/json'
        }
        return headers

    def obtener_usuario_por_dni(self, headers, dni):
        r = requests.get(self.users_api_url + f'/usuario_por_dni/{dni}', verify=self.verify, allow_redirects=False, headers=headers)
        return r.json()

    def obtener_usuarios(self, headers, uids=[]):
        puids = '+'.join(uids)
        r = requests.get(self.users_api_url + f'/usuarios/{puids}', verify=self.verify, allow_redirects=False, headers=headers)
        return r.json()

    def buscar_usuarios(self, headers, search=None):
        if not search:
            return []
        params = {
            'q': search
        }
        r = requests.get(self.users_api_url + f'/usuarios', verify=self.verify, allow_redirects=False, headers=headers, params=params)
        return r.json()
