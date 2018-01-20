from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from model_utils import Base


class ResetClave(Base):

    __tablename__ = 'reset_clave'

    dni = Column(String)
