from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from model_utils import Base


class Mail(Base):

    __tablename__ = 'mails'

    email = Column('email', String)
    confirmado = Column('confirmado',DateTime)
    hash = Column(String)
    eliminado = Column('eliminado', DateTime)

    usuario_id = Column('user_id', String, ForeignKey('users.id'))
    usuario = relationship('Usuario', back_populates='mails')
