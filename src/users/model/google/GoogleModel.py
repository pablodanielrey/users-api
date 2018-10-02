"""
    https://developers.google.com/admin-sdk/directory/v1/quickstart/python
    https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/
"""

import os
import datetime
import uuid
import logging

from users.model.entities import Usuario, Mail, ErrorGoogle
from .GoogleAuthApi import GAuthApis


class GoogleModel:

    dominio_primario = os.environ.get('INTERNAL_DOMAINS').split(',')[0]
    admin = os.environ.get('ADMIN_USER_GOOGLE')
    errores_maximos = 5

    if bool(os.environ.get('GOOGLE_SYNC',0)):
        service = GAuthApis.getServiceAdmin(admin)

    @classmethod
    def _chequear_errores(cls, uid):
        errores = session.query(ErrorGoogle).filter(ErrorGoogle.usuario_id == usuario.id).count()
        return errores > cls.errores_maximos
            

    @classmethod
    def _obtener_usuario_google_id(cls, usuario):
        return '{}@{}'.format(usuario.dni, cls.dominio_primario)

    @classmethod
    def _obtener_alias_para_google(cls, usuario):
        ''' todos los correos que sean igual al dominio primario, estén confirmados y no eliminados '''
        return [
            m.email for m in usuario.mails 
            if m.confirmado and 
                m.eliminado is None and 
                m.email.split('@')[1] in cls.dominio_primario
        ]

    @classmethod
    def actualizar_o_crear_usuario_en_google(cls, session, usuario):
        usuario_google = cls._obtener_usuario_google_id(usuario)

        u = None
        r = None
        try:
            """ https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/admin_directory_v1.users.html """
            u = cls.service.users().get(userKey=usuario_google).execute()
        except Exception as e:
            ''' el usuario no existe '''
            pass

        if u is not None:
            if u['name']['givenName'] != usuario.nombre or u['name']['familyName'] != usuario.apellido:
                datos = {
                    'familyName': usuario.apellido, 
                    'givenName': usuario.nombre, 
                    'fullName': '{} {}'.format(usuario.nombre, usuario.apellido)
                }
                r = cls.service.users().update(userKey=usuario_google,body=datos).execute()

        else:
            aliases = cls._obtener_alias_para_google(usuario)

            datos = {}
            datos["aliases"] = aliases
            datos["changePasswordAtNextLogin"] = False
            datos["primaryEmail"] = usuario_google
            datos["emails"] = [{'address': usuario_google, 'primary': True, 'type': 'work'}]
            for a in aliases:
                datos['emails'].append({'address': a, 'primary': False, 'type': 'work'})

            datos["name"] = {
                "givenName": usuario.nombre, 
                "familyName": usuario.apellido,
                "fullName": '{} {}'.format(usuario.nombre, usuario.apellido)
            }
            datos["password"] = str(uuid.uuid4()).replace('-','')
            datos["externalIds"] = [{'type': 'custom', 'value': usuario.id}]

            r = cls.service.users().insert(body=datos).execute()

        return r

    @classmethod
    def actualizar_correos_hacia_google(cls, session, usuario):
        cs = cls._obtener_alias_para_google(usuario)
        if len(cs) <= 0:
            return []

        username = '{}@{}'.format(usuario.dni,cls.dominio_primario)
        r = cls.service.users().aliases().list(userKey=username).execute()
        aliases = [a['alias'] for a in r.get('aliases', [])]
        aliases_faltantes = [c.strip().lower() for c in cs if c not in aliases]
        respuestas = []
        for e in aliases_faltantes:
            try: 
                r = cls.service.users().aliases().insert(userKey=username, body={"alias":e}).execute()
                respuestas.append(r)

            except Exception as e:
                er = ErrorGoogle()
                er.usuario_id = usuario.id
                er.error = e.resp.status
                er.descripcion = e.resp.reason
                session.add(er)
                respuestas.append(er)
        return respuestas

    @classmethod
    def actualizar_correos_desde_google(cls, session, usuario):
        username = '{}@{}'.format(usuario.dni,cls.dominio_primario)
        r = cls.service.users().aliases().list(userKey=username).execute()
        aliases = [a['alias'] for a in r.get('aliases', [])]

        if len(aliases) <= 0:
            return []

        ret = []
        cs = [c.email for c in usuario.mails if c.confirmado and not c.eliminado]
        correos_a_agregar = [a for a in aliases if a not in cs]
        for c in correos_a_agregar:
            m = Mail()
            m.confirmado = datetime.datetime.now()
            m.email = c
            m.usuario_id = usuario.id
            session.add(m)
            usuario.mails.append(m)
            ret.append({ 'correo': c, 'agregado': True})
        return ret

    @classmethod
    def _sincronizar(cls, session, u):
        r1 = cls.actualizar_o_crear_usuario_en_google(session, u)

        r2 = cls.actualizar_correos_desde_google(session,u)
        session.commit()

        r3 = cls.actualizar_correos_hacia_google(session,u)
        session.commit()
        return {'sincronizacion_usuario': [r1] + r2 + r3 }

    @classmethod
    def sincronizar(cls, session, uid):
        assert uid is not None
        u = session.query(Usuario).filter(Usuario.id == uid).one()
        return cls._sincronizar(session, u)

    @classmethod
    def sincronizar_dirty(cls, session):
        ''' sincroniza todos los usuarios que esten marcados para google '''
        usuarios = session.query(Usuario).filter(Usuario.google == True).all()
        sincronizados = []
        for u in usuarios:
            try:
                if cls._chequear_errores(usuario.id):
                    continue
                ru = cls._sincronizar(session, u)
                u.google = False
                session.commit()
                sincronizados.append(ru)
            except Exception as e:
                logging.exception(e)

        return {
            'usuarios': sincronizados,
            'sincronizados': len(sincronizados)
        }



    """

    @classmethod
    def actualizar_usuario(cls, usuario):
        userGoogle = '{}@{}'.format(dni,self.dominio_primario)
        datos = {
            'familyName': usuario.apellido, 
            'givenName': usuario.nombre, 
            'fullName': '{} {}'.format(usuario.nombre, usuario.apellido)
        }
        r = service.users().update(userKey=userGoogle,body=datos).execute()

        r = service.users().aliases().insert(userKey=userGoogle,body={"alias":e}).execute()


        
        aliases_faltantes = []

        for e in s.emails.split(","):
            if e not in aliases:
                logging.debug('creando alias')
                r = service.users().aliases().insert(userKey=userGoogle,body={"alias":e}).execute()

    @classmethod
    def insertar_usuario(cls):
        # crear usuario
        datos = {}
        datos["aliases"] = s.emails.split(",")
        datos["changePasswordAtNextLogin"] = False
        datos["primaryEmail"] = userGoogle
        datos["emails"] = [{'address': userGoogle, 'primary': True, 'type': 'work'}]

        datos["name"] = {"givenName": user["nombre"], "fullName": fullName, "familyName": user["apellido"]}
        datos["password"] = s.clave
        datos["externalIds"] = [{'type': 'custom', 'value': s.id}]

        r = service.users().insert(body=datos).execute()


        # crear alias
        for e in s.emails.split(","):
            print("Correo a agregar enviar como:{}".format(e))
            r = service.users().aliases().insert(userKey=userGoogle,body={"alias":e}).execute()        


    @classmethod
    def agregarAliasEnviarComo(cls, session, name, email, userKeyG):
        alias = {
            'displayName': name,
            'replyToAddress': email,
            'sendAsEmail': email,
            'treatAsAlias': True,
            'isPrimary': False,
            'isDefault': True
        }
        print("enviar como:{}".format(name))
        print("alias:{}".format(alias))
        gmail = GAuthApis.getServiceGmail(userKeyG)

        r = gmail.users().settings().sendAs().list(userId='me').execute()
        aliases = [ a['sendAsEmail'] for a in r['sendAs'] ]
        print('alias encontrados : {} '.format(aliases))


        if alias['sendAsEmail'] not in aliases:
            print('creando alias')
            r = gmail.users().settings().sendAs().create(userId='me', body=alias).execute()
            ds = cls._crearLog(r)
            session.add(ds)
            session.commit()

    """
