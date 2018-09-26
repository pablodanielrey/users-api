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
    google = Column(Boolean)
    dirty = Column(Boolean)
    avatar = Column(String)
    legajo = Column(String, unique=True)

    mails = relationship('Mail', back_populates='usuario')
    telefonos = relationship('Telefono', back_populates='usuario')

    def mails_alternativos(self, dominio):
        for m in self.mails:
            if m.eliminado:
                continue
            if m.confirmado and dominio not in m.email:
                return m
        return None

