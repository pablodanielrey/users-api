from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from model_utils import Base

class Telefono(Base):

    __tablename__ = 'telephones'

    numero = Column('type', String)
    tipo = Column('number', String)

    usuario_id = Column('user_id', String, ForeignKey('users.id'))
    usuario = relationship('Usuario', back_populates='telefonos')
