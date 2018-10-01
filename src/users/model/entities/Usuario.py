import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, func, or_
from sqlalchemy.orm import relationship

from model_utils import Base

class Usuario(Base):

    __tablename__ = 'usuarios'

    dni = Column(String, unique=True, nullable=False)
    nombre = Column(String)
    apellido = Column(String)
    genero = Column(String)
    nacimiento = Column(Date)
    ciudad = Column(String)
    pais = Column(String)
    direccion = Column(String)
    tipo = Column(String)

    avatar = Column(String)
    legajo = Column(String, unique=True)

    eliminado = Column(DateTime)

    google = Column(Boolean)
    dirty = Column(Boolean)

    mails = relationship('Mail', back_populates='usuario')
    telefonos = relationship('Telefono', back_populates='usuario')
