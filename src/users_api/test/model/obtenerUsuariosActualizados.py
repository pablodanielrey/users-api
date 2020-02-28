import os
import base64
import requests

from pprint import pprint

from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm import sessionmaker

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, contains_eager
import datetime

import json

from model_utils import Base
from users.model.entities import *


EMAILS_API_URL = os.environ['EMAILS_API_URL']

engine = create_engine('postgresql://{}:{}@{}:5432/{}'.format(
    os.environ['USERS_DB_USER'],
    os.environ['USERS_DB_PASSWORD'],
    os.environ['USERS_DB_HOST'],
    os.environ['USERS_DB_NAME']
), echo=True)

Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

if __name__ == '__main__':

    fecha = datetime.datetime.now() - datetime.timedelta(hours=24)

    session = Session()
    q = session.query(Usuario)
    q = q.options(joinedload('telefonos'))
    q = q.join(Mail).filter(Mail.eliminado == None).options(contains_eager(Usuario.mails))
    q = q.join(UsuarioClave).filter(
        and_(
            UsuarioClave.eliminada == None,
            or_(
                Usuario.actualizado >= fecha,
                Usuario.creado >= fecha,
                UsuarioClave.actualizado >= fecha,
                UsuarioClave.creado >= fecha
                )
            )
        ).options(contains_eager(Usuario.claves))

    for c in q.all():
        pprint(c.__json__())
