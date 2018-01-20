import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, func, or_
from sqlalchemy.orm import relationship

from model_utils import Base

class Usuario(Base):

    __tablename__ = 'users'
    __table_args__ = ({'schema': 'profile'})

    dni = Column('dni', String)
    nombre = Column('name', String)
    apellido = Column('lastname', String)
    genero = Column('gender', String)
    nacimiento = Column('birthdate', Date)
    ciudad = Column('city', String)
    pais = Column('country', String)
    direccion = Column('address', String)
    tipo = Column('type', String)
    google = Column('google', Boolean)
    avatar = Column(String)

    mails = relationship('Mail', back_populates='usuario')
    telefonos = relationship('Telefono', back_populates='usuario')
    claves = relationship('UsuarioClave', back_populates='usuario')

    def mails_alternativos(self, dominio):
        for m in self.mails:
            if m.eliminado:
                continue
            if m.fecha_confirmado and dominio not in m.email:
                return m
        return None

    """


    @property
    def age(self):
        if not self.birthdate:
            return 0
        today = datetime.datetime.now()
        born = self.birthdate
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @classmethod
    def search(cls, s, regex):
        ''' busca por nombre, apellido o dni personas '''
        regs = regex.split(' ')
        terms = []
        for r in regs:
            terms.append(cls.name.ilike('{}{}{}'.format('%',r,'%')))
            terms.append(cls.lastname.ilike('{}{}{}'.format('%',r,'%')))
            terms.append(cls.dni.ilike('{}{}{}'.format('%',r,'%')))
        q = s.query(cls).filter(or_(*terms))
        return q
    """

"""
class Student(User, Entity):

    def __init__(self):
        super().__init__()
        self.studentNumber = None
        self.condition = None
"""
