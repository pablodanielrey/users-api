import os
import datetime

from users.model.entities import Usuario, Mail
from .GoogleAuthApi import GAuthApis


class GoogleModel:

    dominio_primario = os.environ.get('INTERNAL_DOMAINS').split(',')[0]
    admin = os.environ.get('ADMIN_USER_GOOGLE')
    service = GAuthApis.getServiceAdmin(admin)

    @classmethod
    def actualizar_correos_hacia_google(cls, usuario):
        cs = [c.email for c in usuario.mails if c.confirmado and not c.eliminado and cls.dominio_primario in c.email]
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
                r = {
                    'error': e.resp.status,
                    'response': e.resp.reason
                }
                respuestas.append(r)
        return respuestas

    @classmethod
    def actualizar_correos_desde_google(cls, session, usuario):

        username = '{}@{}'.format(usuario.dni,cls.dominio_primario)
        r = cls.service.users().aliases().list(userKey=username).execute()
        aliases = [a['alias'] for a in r.get('aliases', [])]

        if len(aliases) <= 0:
            return []

        ret = []
        cs = [c.email for c in usuario.mails if c.confirmado and not c.eliminado and cls.dominio_primario in c.email]
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
    def sincronizar(cls, session, uid):
        assert uid is not None
        u = session.query(Usuario).filter(Usuario.id == uid).one()
        r = cls.actualizar_correos_desde_google(session,u)
        session.commit()
        r2 = cls.actualizar_correos_hacia_google(u)



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
