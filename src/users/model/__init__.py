import os
import base64
import requests
import logging
import threading

from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm import sessionmaker

from model_utils import Base
from .entities import *

EMAILS_API_URL = os.environ['EMAILS_API_URL']

engine = create_engine('postgresql://{}:{}@{}:5432/{}'.format(
    os.environ['USERS_DB_USER'],
    os.environ['USERS_DB_PASSWORD'],
    os.environ['USERS_DB_HOST'],
    os.environ['USERS_DB_NAME']
), echo=True)

Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

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

def crear_tablas():
    #engine.execute(CreateSchema('users'))
    Base.metadata.create_all(engine)

from .UsersModel import UsersModel
from .ResetClaveModel import ResetClaveModel

__all__ = [
    'UsersModel',
    'ResetClaveModel'
]
