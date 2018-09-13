from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from model_utils import Base

class UsuarioClave(Base):

    __tablename__ = 'user_password'

    nombre_de_usuario = Column('username', String)
    clave = Column('password', String)
    expiracion = Column(DateTime)
    eliminada = Column(DateTime)
    debe_cambiarla = Column(Boolean, default=False)

    usuario_id = Column('user_id', String)
