import sys
import csv
import re
from dateutil.parser import parse
import logging
logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':

    from users.model import obtener_session, UsersModel

    reg = re.compile('[A|B|C|D|E]+.*')
    
    archivo = sys.argv[1]
    with open(archivo,'r') as f:
        c = csv.reader(f, delimiter=',', quotechar="\"")
        with obtener_session() as s:
            for r in c:
                cargo = r[7].strip()

                if cargo == 'Clase Grupo':
                    continue

                dni = r[1].strip().lower()
                nacimiento = parse(r[19])
                n = r[2].split(',')
                nombre = ''
                apellido = ''
                if len(n) >= 2:
                    apellido = n[0].strip().capitalize()
                    nombre = n[1].strip().capitalize()
                else:
                    nombre = n[0].strip().capitalize()

                r = {
                    'cargo': cargo,
                    'dni': dni,
                    'nombre': nombre,
                    'apellido': apellido,
                    'nacimiento': nacimiento
                }
                
                #m = reg.match(cargo)
                #if m:
                u = UsersModel.usuario_por_dni(s, dni=dni)
                if not u:
                    logging.debug('{} {} {} no existe, se crea la persona'.format(dni, nombre, apellido))
                    UsersModel.crear_usuario(s,r)
                    s.commit()
                else:
                    logging.debug('{} {} {} ya existe, se actualiza'.format(dni, nombre, apellido))
                    uid = u.id
                    logging.debug(r)
                    UsersModel.actualizar_usuario(s, uid, r)
                    s.commit()
                        