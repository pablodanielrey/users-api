import os
import uuid
import datetime
import base64
import requests
import logging

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, contains_eager

from . import obtener_template, enviar_correo
from .exceptions import *
from .entities import *


class UsersModel:

    VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL', 1)))
    FILES_API_URL = os.environ['FILES_API_URL']

    @staticmethod
    def _aplicar_filtros_comunes(q, offset, limit):
        q = q.offset(offset) if offset else q
        q = q.limit(limit) if limit else q
        return q


    @classmethod
    def obtener_avatar(cls, hash):
        avatar = None
        url = cls.FILES_API_URL + '/archivo/' + hash + '/contenido'
        resp = requests.get(url, verify=cls.VERIFY_SSL)
        if resp.status_code != 200:
            ''' pruebo obtener una imagen por defecto '''
            with open('users/model/templates/avatar.png', 'rb') as f:
                avatar = {
                    'name': 'default',
                    'data': base64.b64encode(f.read()).decode('utf-8'),
                    'content-type': resp.headers['Content-Type']
                }
        else:
            avatar = {
                'name': 'default',
                'data': base64.b64encode(resp.content).decode('utf-8'),
                'content-type': resp.headers['Content-Type']
            }
        return avatar

    @classmethod
    def actualizar_avatar(cls, hash, contenido):
        url = cls.FILES_API_URL + '/archivo/' + hash + '.json'
        resp = requests.post(url=url, json={'id':hash, 'data':contenido}, verify=cls.VERIFY_SSL)
        if resp.status_code != 200:
            raise UsersError()


    @classmethod
    def login(cls, session, usuario, clave):
         return session.query(UsuarioClave).filter(UsuarioClave.nombre_de_usuario == usuario, UsuarioClave.clave == clave).one()


    @classmethod
    def claves(cls, session, uid=None, cid=None, limit=None, offset=None):
        q = session.query(UsuarioClave)
        q = q.filter(UsuarioClave.id == cid) if cid else q
        q = q.filter(UsuarioClave.usuario_id == uid) if uid else q
        cls._aplicar_filtros_comunes(q, offset, limit)
        q.order_by(UsuarioClave.actualizado.desc(), UsuarioClave.creado.desc())
        return q.all()

    @classmethod
    def cambiar_clave(cls, session, uid, clave):
        '''
            IMPORANTE!!!!:
            como ahora no todos los sistemas soportan varias claves en el registro de claves. se elimina la clave anterior.
            por lo que no queda historial ni eliminación lógica de la clave!!!!
            cuando todos los sistemas estén usando el nuevo esquema se cambia este método para registrar el historial de claves.
        '''
        assert uid is not None

        if not clave:
            raise FormatoDeClaveIncorrectoError()

        if len(clave) < 8:
            raise FormatoDeClaveIncorrectoError()

        """
        uclave = session.query(UsuarioClave).filter(UsuarioClave.usuario_id == uid, UsuarioClave.eliminada == None).one_or_none()
        if uclave:
            uclave.eliminada = datetime.datetime.now()

        uuclave = UsuarioClave(usuario_id=uid, nombre_de_usuario=dni, clave=clave)
        session.add(uuclave)
        """
        uclave = session.query(UsuarioClave).filter(UsuarioClave.usuario_id == uid).one_or_none()
        if uclave:
            uclave.clave = clave
            uclave.actualizado = datetime.datetime.now()
            uclave.debe_cambiarla = False
        else:
            dni = session.query(Usuario.dni).filter(Usuario.id == uid).one()
            uuclave = UsuarioClave(usuario_id=uid, nombre_de_usuario=dni, clave=clave)
            uuclave.debe_cambiarla = False
            session.add(uuclave)

        session.commit()

        '''
            lo siguiente debo hacerlo con eventos para desacoplar sistemas y microservicios
        try:
            sincronizar_usuario(uclave.usuario_id)
        except Exception as e:
            logging.debug(e)
        '''

    @classmethod
    def generar_clave(cls, session, uid):
        assert uid is not None
        logging.debug(uid)
        clave=str(uuid.uuid4()).replace('-','')[0:8]
        uclave = session.query(UsuarioClave).filter(UsuarioClave.usuario_id == uid).one_or_none()
        if uclave:
            uclave.clave = clave
            uclave.actualizado = datetime.datetime.now()
            uclave.debe_cambiarla = True
        else:
            q = session.query(Usuario).filter(Usuario.id == uid)
            u = q.one_or_none()
            if not u:
                raise UsersError(status_code=404)
            uuclave = UsuarioClave(usuario_id=uid, nombre_de_usuario=u.dni, clave=clave)
            uuclave.debe_cambiarla = True
            session.add(uuclave)
        return clave

    @classmethod
    def crear_usuario(cls, session, usuario):
        dni = usuario['dni']
        if not dni:
            raise Exception('dni = null')
        if ' ' in dni:
            raise Exception('dni con caracteres inválidos')
        dni = dni.replace('.','').lower()

        if session.query(Usuario).filter(Usuario.dni == dni).count() > 0:
            raise Exception('Usuario existente')

        u = Usuario()
        u.id = str(uuid.uuid4())
        u.nombre = usuario['nombre']
        u.apellido = usuario['apellido']
        u.dni = dni

        if 'legajo' in usuario:
            legajo = usuario['legajo']
            if legajo:
                legajo = legajo.replace(' ','')
                if legajo == '':
                    raise Exception('legajo inválido')

                if session.query(Usuario).filter(Usuario.legajo == legajo).count() > 0:
                    raise Exception('Legajo existente')

                u.legajo = legajo

        session.add(u)
        return u.id

    @classmethod
    def actualizar_usuario(cls, session, uid, datos):
        assert uid is not None

        import re
        g = re.match('((\w)*\s*)*', datos['nombre'])
        if not g:
            raise FormatoIncorrecto()
        nombre = g.group()

        g2 = re.match('((\w)*\s*)*', datos['apellido'])
        if not g:
            raise FormatoIncorrecto()
        apellido = g2.group()

        usuario = session.query(Usuario).filter(Usuario.id == uid).one()
        usuario.nombre = nombre
        usuario.apellido = apellido
        if 'legajo' in datos:
            usuario.legajo = datos['legajo']
        if 'genero' in datos:
            usuario.genero = datos['genero']
        if 'direccion' in datos:
            usuario.direccion = datos['direccion']
        if 'ciudad' in datos:
            usuario.ciudad = datos['ciudad']
        if 'pais' in datos:
            usuario.pais = datos['pais']

    @classmethod
    def usuario(cls, session, uid=None, dni=None, retornarClave=False):
        q = session.query(Usuario)
        if uid:
            q = q.filter(Usuario.id == uid)

        if dni:
            q = q.filter(Usuario.dni == dni)

        if retornarClave:
            q = q.join(UsuarioClave).filter(UsuarioClave.eliminada == None).options(contains_eager(Usuario.claves))
        q = q.options(joinedload('mails'), joinedload('telefonos'))
        q = q.filter(Telefono.eliminado == None)
        return q.one()


    @classmethod
    def encontrarUsuariosModificadosDesde(cls, session, fecha, offset=None, limit=None):
        q = session.query(Usuario)
        q = q.filter(or_(Usuario.actualizado >= fecha, Usuario.creado >= fecha))

        q3 = session.query(UsuarioClave.usuario_id).filter(or_(UsuarioClave.actualizado >= fecha, UsuarioClave.creado >= fecha, UsuarioClave.eliminada >= fecha))
        q2 = session.query(Usuario).filter(Usuario.id.in_(q3))

        q4 = session.query(Mail.usuario_id).filter(or_(Mail.actualizado >= fecha, Mail.creado >= fecha, Mail.eliminado >= fecha))
        q5 = session.query(Usuario).filter(Usuario.id.in_(q4))

        q = q.union(q2).union(q5)

        q = q.options(joinedload('telefonos'), joinedload('mails'), joinedload('claves'))
        q = cls._aplicar_filtros_comunes(q, offset, limit)
        return q.all()


    @classmethod
    def encontrarUsuariosPorSearch(cls, session, search, retornarClave=False, offset=None, limit=None):
        q = session.query(Usuario)
        q = q.filter(or_(\
            Usuario.dni.op('~*')(search),\
            Usuario.nombre.op('~*')(search),\
            Usuario.apellido.op('~*')(search)\
        )) if search else q

        if retornarClave:
        #    #q = q.join(UsuarioClave).filter(or_(Usuario.claves == None, UsuarioClave.eliminada == None)).options(contains_eager(Usuario.claves))
        #    q = q.join(UsuarioClave).options(contains_eager(Usuario.claves))
            q = q.options(joinedload('claves'))

        q = q.options(joinedload('telefonos'))
        q = q.options(joinedload('mails'))
        #q = q.join(Mail).filter(or_(Usuario.mails == None, Mail.eliminado == None)).options(contains_eager(Usuario.mails))
        #q = q.join(Mail).options(contains_eager(Usuario.mails))
        q = cls._aplicar_filtros_comunes(q, offset, limit)
        return q.all()

    @classmethod
    def usuarios(cls, session, search=None, retornarClave=False, offset=None, limit=None, fecha=None):
        if fecha:
            return cls.encontrarUsuariosModificadosDesde(session, fecha, offset=offset, limit=limit)
        if search:
            return cls.encontrarUsuariosPorSearch(session, search, retornarClave=retornarClave, offset=offset, limit=limit)
        return []


    @classmethod
    def existe(cls, session, usuario):
        if session.query(Usuario).filter(Usuario.id == usuario).count() > 0:
            return True
        return False

    @classmethod
    def correos(cls, session, cid=None, usuario=None, historico=False, offset=None, limit=None):
        q = session.query(Mail)
        q = q.filter(Mail.id == cid) if cid else q
        q = q.filter(Mail.usuario_id == usuario) if usuario else q
        q = q.filter(Mail.eliminado == None) if not historico else q
        q = cls._aplicar_filtros_comunes(q, offset, limit)
        return q.all()

    @classmethod
    def obtener_correo_por_cuenta(cls, session, cuenta):
        q = session.query(Mail).filter(Mail.email == cuenta, Mail.eliminado == None)
        return q.one_or_none()


    @classmethod
    def agregar_correo_institucional(cls, session, uid, datos):
        assert 'email' in datos
        assert len(datos['email'].strip()) > 0

        mails = session.query(Mail).filter(Mail.usuario_id == uid, Mail.email == datos['email'], Mail.eliminado == None).order_by(Mail.creado.desc()).all()
        for m in mails:
            ''' ya existe, no lo agrego pero no tiro error '''
            if not m.confirmado:
                m.confirmado = datetime.datetime.now()
            return m.id

        mail = Mail(email=datos['email'].lower())
        mail.id = str(uuid.uuid4())
        mail.usuario_id = uid
        mail.confirmado = datetime.datetime.now()
        session.add(mail)
        return mail


    @classmethod
    def agregar_correo(cls, session, uid, datos):
        assert 'email' in datos
        assert len(datos['email'].strip()) > 0

        mails = session.query(Mail).filter(Mail.usuario_id == uid, Mail.email == datos['email'], Mail.eliminado == None).order_by(Mail.creado.desc()).all()
        for m in mails:
            ''' ya existe, no lo agrego pero no tiro error '''
            return m.id
        usuario = session.query(Usuario).filter(Usuario.id == uid).one()
        mail = Mail(email=datos['email'].lower())
        mail.id = str(uuid.uuid4())
        usuario.mails.append(mail)
        session.add(mail)
        return mail.id

    @classmethod
    def eliminar_correo(cls, session, cid):
        correo = session.query(Mail).filter(Mail.id == cid).one()
        correo.eliminado = datetime.datetime.now()

    @classmethod
    def eliminar_telefono(cls, session, tid):
        telefono = session.query(Telefono).filter(Telefono.id == tid).one()
        telefono.eliminado = datetime.datetime.now()

    @classmethod
    def confirmar_correo(cls, session, cid, code):
        correo = session.query(Mail).filter(Mail.id == cid, Mail.hash == code, Mail.eliminado == None).order_by(Mail.creado.desc()).first()
        if not correo:
            raise CorreoNoEncontradoError()
        correo.confirmado = datetime.datetime.now()

    @classmethod
    def enviar_confirmar_correo(cls, session, cid):
        correo = session.query(Mail).filter(Mail.id == cid).one()
        if not correo.hash:
            correo.hash=str(uuid.uuid4())[:5]

        mail = correo.email.lower().strip()
        codigo = correo.hash
        nombre = correo.usuario.nombre + ' ' + correo.usuario.apellido
        cuerpo = obtener_template('confirmar_correo.html', nombre, correo.hash)
        enviar_correo('pablo.rey@econo.unlp.edu.ar', mail, 'Confirmación de cuenta alternativa de contacto', cuerpo)


    """
    @staticmethod
    def obtener_template(nombre, codigo):
        with open('users/model/templates/confirmar_correo.html','r') as f:
            template = f.read()
            texto = template.replace('$USUARIO',nombre)\
                    .replace('$CODIGO_CONFIRMACION',codigo)\
                    .replace('$URL_DE_INFORME','http://incidentes.econo.unlp.edu.ar/0293094-df2323-r4354-f34543')
            return texto

    @staticmethod
    def enviar_correo(de, para, asunto, cuerpo):
        ''' https://developers.google.com/gmail/api/guides/sending '''
        bcuerpo = base64.urlsafe_b64encode(cuerpo.encode('utf-8')).decode()
        r = requests.post('http://163.10.56.57:8001/emails/api/v1.0/enviar_correo', json={'de':de, 'para':para, 'asunto':asunto, 'cuerpo':bcuerpo})
        print(str(r))
    """
