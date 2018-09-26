
import os
import psycopg2
import sys
import logging
logging.getLogger().setLevel(logging.DEBUG)
import uuid
import datetime

if __name__ == '__main__':

    if len(sys.argv) < 3:
        logging.info('debe ejecutar el script usando: {} dni nombre apellido'.format(sys.argv[0]))

    dni = sys.argv[1]
    nombre = sys.argv[2]
    apellido = sys.argv[3]

    h = os.environ['USERS_DB_HOST']
    pp = os.environ['USERS_DB_PORT']
    n = os.environ['USERS_DB_NAME']
    u = os.environ['USERS_DB_USER']
    p = os.environ['USERS_DB_PASSWORD']

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = con.cursor()
        try:
            uid = str(uuid.uuid4())
            cur.execute('insert into usuarios (id,nombre,apellido,dni,dirty) values (%s,%s,%s,%s,True)',(uid,nombre,apellido,dni))
            con.commit()
            logging.info('usuario agregado {} {} {}'.format(dni,nombre,apellido))

        except Exception as e:
            con.rollback()
            logging.exception(e)

        finally:
            cur.close()

    finally:
        con.close()