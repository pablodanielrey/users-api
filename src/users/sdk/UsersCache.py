import pymongo
from pymongo.operations import IndexModel

import datetime

class UsersCache:

    def __init__(self, mongo_url, users_api, prefijo='_users_', timeout=60 * 60):
        db = '{}_{}'.format(prefijo, self.__class__.__name__)
        self.mongo = pymongo.MongoClient(mongo_url)[db]
        self.prefijo = prefijo
        self.timeout = timeout
        self.api = users_api

        # indices para la expiración
        for c in ['usuarios']:
            self.mongo.drop_collection(c)
            self.mongo[c].create_index('insertadoEn',expireAfterSeconds=self.timeout)

    def _setear_usuario(self, usuario):
        usuario['insertadoEn'] = datetime.datetime.utcnow()
        self.mongo.usuarios.insert_one(usuario)

    def obtener_usuario_por_dni(self, headers, dni):
        usuario = self.mongo.usuarios.find_one({'dni':dni})
        if not usuario:
            usuarios = self.api.obtener_usuarios([uid],headers)
            if not usuarios or len(usuarios) <= 0:
                return None
            usuario = usuarios[0]
            self._setear_usuario(usuario)
        if '_id' in usuario:
            del usuario['_id']
        return usuario

    def obtener_usuarios(self, headers, uids=[]):
        usuarios = []
        faltantes = []
        for uid in uids:
            usuario = self.mongo.usuarios.find_one({'id':uid})
            if usuario:
                usuarios.append(usuario)
            else:
                faltantes.append(uid)

        if len(faltantes) > 0:            
            fusuarios = self.api.obtener_usuarios(faltantes,headers)
            for usuario in fusuarios:
                self._setear_usuario(usuario)
            usuarios.extend(fusuarios)

        for usuario in usuarios:
            if '_id' in usuario:
                del usuario['_id']

        return usuarios

    def buscar_usuarios(self, headers, search=None):
        return self.api.buscar_usuarios(headers, search)