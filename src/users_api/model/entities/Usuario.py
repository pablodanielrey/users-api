from datetime import datetime, time, timedelta
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, func, or_, ForeignKey
from sqlalchemy.orm import relationship

from model_utils import Base
import pytz


class LogUsuario(Base):

    __tablename__ = 'log_usuario'

    usuario_id = Column(String, ForeignKey('usuarios.id'))
    autorizador_id = Column(String, ForeignKey('usuarios.id'))
    datos = Column(String)


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
    
    def obtener_nacimiento(self, tz):
        return self._localizar_fecha_en_zona(self.nacimiento, tz)

    def _localizar_fecha_en_zona(self, fecha, tz='America/Argentina/Buenos_Aires'):
        if fecha is None:
            return None
        timezone = pytz.timezone(tz)
        dt = datetime.combine(fecha, time(0))
        dt = timezone.localize(dt)
        return dt