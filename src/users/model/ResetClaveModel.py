import uuid
import datetime
import os

import logging
logging.getLogger().setLevel(logging.DEBUG)

from sqlalchemy import or_, and_

from . import Session, UsersModel, obtener_template, enviar_correo, sincronizar_usuario
from .exceptions import *
from .JWTModel import JWTModel
from .entities import *

class ResetClaveModel:

    INTENTOS_POR_DIA = 50

    DECODERS = [
        JWTModel(str(uuid.uuid4()) + str(uuid.uuid4())),
        JWTModel(str(uuid.uuid4()) + str(uuid.uuid4())),
        JWTModel(str(uuid.uuid4()) + str(uuid.uuid4()), 60 * 5),                 # ingresar el código enviado al correo
        JWTModel(str(uuid.uuid4()) + str(uuid.uuid4()), 60)
    ]

    @staticmethod
    def _obtener_correo_alternativo(usuario):
        for c in usuario.mails:
            if 'econo.unlp.edu.ar' not in c.email:
                return c
        return None

    """
    @classmethod
    def _test_encode_token(cls, encoder):
        ''' metodo de testeo para debug de la app '''
        return cls.DECODERS[encoder].encode_auth_token({'algo_de':'prueba', 'y_otra':'cosa'})
    """

    @classmethod
    def _test_decode_token(cls, encoder, token):
        ''' metodo de testeo para debug de la app '''
        return cls.DECODERS[encoder].decode_auth_token(token)

    @classmethod
    def verificaciones(cls, solo_pendientes=True, limit=None, offset=None):
        session = Session()
        try:
            q = session.query(ResetClaveCodigo)
            q = q.filter(ResetClaveCodigo.verificado == None, ResetClaveCodigo.expira >= datetime.datetime.now()) if solo_pendientes else q
            q = q.limit(limit) if limit else q
            q = q.offset(offset) if offset else q
            q = q.order_by(ResetClaveCodigo.creado.desc(), ResetClaveCodigo.actualizado.desc())
            return q.all()

        finally:
            session.close()

    @classmethod
    def obtener_token(cls):
        try:
            token = cls.DECODERS[0].encode_auth_token()
            return {'estado':'ok', 'token':token}
        except Exception:
            raise ResetClaveError()

    @classmethod
    def obtener_usuario(cls, session, token, dni):
        assert token is not None
        try:
            cls.DECODERS[0].decode_auth_token(token)
        except Exception as e:
            raise TokenExpiradoError()

        ''' intentos de recuperación por día '''
        ayer = (datetime.datetime.now() - datetime.timedelta(hours=24)).replace(hour=0,second=0,minute=0)
        intentos = session.query(ResetClave).filter(and_(ResetClave.dni == dni, ResetClave.creado >= ayer)).count()
        if intentos > cls.INTENTOS_POR_DIA:
            raise LimiteDeVerificacionError()

        rc = ResetClave(dni=dni)
        session.add(rc)
        session.commit()

        usuario = UsersModel.usuario(session, dni=dni)
        #usuario = session.query(Usuario).filter(Usuario.dni == dni).one_or_none()
        if not usuario:
            raise UsuarioNoEncontradoError()

        correo = usuario.mails_alternativos('econo.unlp.edu.ar')
        if not correo:
            raise NoTieneCuentaAlternativaError()

        rusuario = {
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'dni': usuario.dni,
            'correo': {
                    'email': correo.email
                }
        }
        nuevo_token = cls.DECODERS[1].encode_auth_token(datos=rusuario)
        r = { 'estado': 'ok',
              'usuario':rusuario,
              'token': nuevo_token}
        return r

    @classmethod
    def enviar_codigo(cls, token):
        assert token is not None
        datos = None
        try:
            datos = cls.DECODERS[1].decode_auth_token(token)
        except Exception as e:
            raise TokenExpiradoError()

        session = Session()
        try:
            dni = datos['dni']
            correo = datos['correo']['email']

            ahora = datetime.datetime.now()
            esperaEnvio = ahora - datetime.timedelta(hours=5)

            rcs = session.query(ResetClaveCodigo).filter(ResetClaveCodigo.dni == dni, ResetClaveCodigo.correo == correo).order_by(ResetClaveCodigo.expira.desc()).all()
            rc = None
            for r in rcs:
                if r.expira < ahora:
                    continue

                if r.verificado:
                    continue

                ''' tengo el primer codigo que no ha expirado '''
                r.expira = ahora + datetime.timedelta(days=1)

                rc = r
                break
            else:
                rc = ResetClaveCodigo(nombre = datos['nombre'] + ' ' + datos['apellido'],
                                      dni = datos['dni'],
                                      codigo = str(uuid.uuid4())[:5],
                                      correo = datos['correo']['email'],
                                      expira = ahora + datetime.timedelta(days=1))
                session.add(rc)
            session.commit()

            if not rc.enviado or rc.enviado <= esperaEnvio:
                temp = obtener_template('reset_clave.html', rc.nombre, rc.codigo)
                r = enviar_correo('sistemas@econo.unlp.edu.ar', rc.correo, 'Código de confirmación de cambio de contraseña', temp)
                if not r.ok:
                    raise EnvioCodigoError()
                rc.enviado = ahora
                session.commit()

            nuevo_token = cls.DECODERS[2].encode_auth_token(datos=rc.id)
            return { 'estado':'ok', 'token': nuevo_token }

        except Exception as e:
            raise EnvioCodigoError()

        finally:
            session.close()

    @classmethod
    def verificar_codigo(cls, token, codigo):
        assert token is not None
        rcid = None
        try:
            rcid = cls.DECODERS[2].decode_auth_token(token)
        except Exception as e:
            raise TokenExpiradoError()

        session = Session()
        try:
            ahora = datetime.datetime.now()
            rc = session.query(ResetClaveCodigo).filter(ResetClaveCodigo.id == rcid, ResetClaveCodigo.expira >= ahora).one_or_none()
            if not rc:
                raise TokenExpiradoError()

            if rc.verificado:
                raise TokenExpiradoError()

            if rc.intentos > 10:
                rc.expira = ahora
                session.commit()
                raise LimiteDeVerificacionError()

            if rc.codigo != codigo:
                rc.intentos = rc.intentos + 1
                session.commit()
                raise CodigoIncorrectoError()

            rc.verificado = ahora
            rc.expira = ahora
            session.commit()

            nuevo_token = cls.DECODERS[3].encode_auth_token(datos=rc.dni)
            return { 'estado':'ok', 'token': nuevo_token }

        finally:
            session.close()


    @classmethod
    def cambiar_clave(cls, session, token, clave):
        assert token is not None
        dni = None
        try:
            dni = cls.DECODERS[3].decode_auth_token(token)
        except Exception as e:
            logging.debug(e)
            raise TokenExpiradoError()

        try:
            usuario = UsersModel.usuario(session, dni=dni)
            UsersModel.cambiar_clave(session, usuario.id, clave)
            session.commit()
        except UsersError as e1:
            logging.debug(e1)
            raise e1
        except Exception as e:
            logging.debug(e)
            raise ClaveError()

        try:
            sincronizar_usuario(usuario.id)
        except Exception as e:
            logging.debug(e)

        return { 'estado': 'ok', 'mensaje': 'contraseña cambiada con éxito', 'codigo': 0 }
