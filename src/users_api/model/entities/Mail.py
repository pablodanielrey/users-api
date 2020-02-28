from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from model_utils import Base


class Mail(Base):

    __tablename__ = 'mails'

    email = Column(String)
    confirmado = Column(DateTime)
    hash = Column(String)
    eliminado = Column(DateTime)

    usuario_id = Column(String, ForeignKey('usuarios.id'))
    usuario = relationship('Usuario', back_populates='mails')
