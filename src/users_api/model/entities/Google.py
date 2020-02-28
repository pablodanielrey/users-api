import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, func, or_
from sqlalchemy.orm import relationship

from model_utils import Base

class ErrorGoogle(Base):

    __tablename__ = 'error_google'

    usuario_id = Column(String)
    error = Column(String)
    descripcion = Column(String)

class RespuestaGoogle(Base):

    __tablename__ = 'respuesta_google'

    usuario_id = Column(String)
    respuesta = Column(String)
