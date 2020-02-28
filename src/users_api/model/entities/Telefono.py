from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from model_utils import Base

class Telefono(Base):

    __tablename__ = 'telefonos'

    numero = Column(String)
    tipo = Column(String)
    actualizado = Column(DateTime)
    eliminado = Column(DateTime)

    usuario_id = Column(String, ForeignKey('usuarios.id'))
    usuario = relationship('Usuario', back_populates='telefonos')


