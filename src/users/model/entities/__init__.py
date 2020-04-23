import uuid
from sqlalchemy import Column, String, DateTime, func, desc
from sqlalchemy.ext.declarative import declarative_base
from flask_jsontools import JsonSerializableBase

def generateId():
    return str(uuid.uuid4())

class MyBaseClass:

    id = Column(String, primary_key=True, default=generateId)
    creado = Column(DateTime, server_default=func.now())
    actualizado = Column(DateTime, onupdate=func.now())

    def __init__(self):
        self.id = generateId()

    @classmethod
    def findAll(cls, s):
        return s.query(cls).all()

Base = declarative_base(cls=(JsonSerializableBase,MyBaseClass))

from .Usuario import Usuario, LogUsuario
from .Mail import Mail
from .Telefono import Telefono
from .Google import RespuestaGoogle, ErrorGoogle

__all__ = [
    'Usuario', 'LogUsuario',
    'Mail',
    'Telefono',
    'RespuestaGoogle',
    'ErrorGoogle'
]