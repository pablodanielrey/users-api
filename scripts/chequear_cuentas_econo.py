import logging
logging.getLogger().setLevel(logging.INFO)
import os
from sqlalchemy import or_
import re
import csv
from users.model import obtener_session
from users.model.entities import Mail, Usuario
from users.model.google.GoogleAuthApi import GAuthApis

import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
admin = os.environ.get('ADMIN_USER_GOOGLE')
google_service = GAuthApis.getServiceAdmin(admin)


def check_google(usuario):
    usuario_google = '{}@econo.unlp.edu.ar'.format(usuario.dni)
    logging.info("Chequeando en google el usuario: {}".format(usuario_google))
    try:
        """ https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/admin_directory_v1.users.html """
        u = google_service.users().get(userKey=usuario_google).execute()
        return u
    except Exception:
        ''' el usuario no existe '''
        return None

if __name__ == '__main__':
        
    expr = "[\w]+@(depeco.){0,1}econo.unlp.edu.ar"        
    users_in_google = 0
    users_not_in_google = 0
    with obtener_session() as session:
        uids = session.query(Mail.usuario_id).filter(Mail.eliminado == None, or_(Mail.email.like('%@econo.unlp.edu.ar'), Mail.email.like('%@depeco.econo.unlp.edu.ar'))).distinct().all()        
        users = session.query(Usuario).filter(Usuario.id.in_(uids)).all()                        
        with open('/tmp/check_mails_google.csv', 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(['ID','DNI','EMAIL', 'EN GOOGLE', 'ALIAS EN GOOGLE'])            
            actual = 0
            total = len(uids)
            logging.info("Cantidad de usuarios: {}".format(total))
            for u in users:
                actual += 1
                logging.info("{}/{} Procesando el usuario {}".format(actual, total,"{} {}".format(u.nombre, u.apellido)))        

                user_google = check_google(u)
                mails_econo = ' '.join([m.email for m in u.mails if m.eliminado is None and re.search(expr, m.email)])
                if not user_google:
                    logging.info("No esta en google")
                    users_not_in_google += 1
                    row = [u.id, u.dni, mails_econo, 'No', '']
                    writer.writerow(row)   
                else:
                    logging.info("Esta en google")
                    users_in_google += 1
                    alias = [m['address'] for m in user_google['emails'] if m['address'].split('@')[0] != u.dni]
                    row = [u.id, u.dni, mails_econo, 'Si', ' '.join(alias)]
                    writer.writerow(row)                                     
    logging.info("Cantidad de usuarios en google: {}".format(users_in_google))
    logging.info("Cantidad de usuarios que no estan en google: {}".format(users_not_in_google))
    
