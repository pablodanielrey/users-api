import os
import base64
import requests
import logging
import threading

import contextlib

from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm import sessionmaker

from model_utils import Base
from .entities import *

EMAILS_API_URL = os.environ['EMAILS_API_URL']


@contextlib.contextmanager
def obtener_session():
    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
        os.environ['USERS_DB_USER'],
        os.environ['USERS_DB_PASSWORD'],
        os.environ['USERS_DB_HOST'],
        os.environ['USERS_DB_PORT'],
        os.environ['USERS_DB_NAME']
    ), echo=False)

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def obtener_template(template, nombre, codigo):
    with open('users/model/templates/' + template,'r') as f:
        template = f.read()
        texto = template.replace('$USUARIO',nombre)\
                .replace('$CODIGO_CONFIRMACION',codigo)\
                .replace('$URL_DE_INFORME','http://incidentes.econo.unlp.edu.ar/0293094-df2323-r4354-f34543')
        return texto

def enviar_correo(de, para, asunto, cuerpo):
    ''' https://developers.google.com/gmail/api/guides/sending '''
    bcuerpo = base64.urlsafe_b64encode(cuerpo.encode('utf-8')).decode()
    r = requests.post(EMAILS_API_URL + '/correos/', json={'sistema':'users', 'de':de, 'para':para, 'asunto':asunto, 'cuerpo':bcuerpo})
    return r


from .UsersModel import UsersModel

__all__ = [
    'UsersModel'
]
