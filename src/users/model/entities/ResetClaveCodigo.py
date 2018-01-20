from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from model_utils import Base


class ResetClaveCodigo(Base):

    __tablename__ = 'reset_clave_codigo'
    
    dni = Column(String)
    nombre = Column(String)
    codigo = Column(String)
    correo = Column(String)
    expira = Column(DateTime)
    enviado = Column(DateTime)
    verificado = Column(DateTime)
    intentos = Column(Integer, default=0)
