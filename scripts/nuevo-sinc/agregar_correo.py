
import os
import psycopg2
import sys
import logging
logging.getLogger().setLevel(logging.DEBUG)
import uuid
import datetime

if __name__ == '__main__':

    if len(sys.argv) < 3:
        logging.info('debe ejecutar el script usando: {} dni correo'.format(sys.argv[0]))

    dni = sys.argv[1]
    correo = sys.argv[2]

    h = os.environ['USERS_DB_HOST']
    pp = os.environ['USERS_DB_PORT']
    n = os.environ['USERS_DB_NAME']
    u = os.environ['USERS_DB_USER']
    p = os.environ['USERS_DB_PASSWORD']

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = con.cursor()
        try:
            cur.execute('select usuario_id from usuarios where dni = %s', (dni,))
            uid = cur.fetchone()[0]

            eid = str(uuid.uuid4())
            cur.execute('insert into mails (id,usuario_id,email,confirmado) values (%s,%s,%s,NOW())',(eid,uid,correo))
            cur.execute('update usuarios set dirty = %s where id = %s', (True,uid))

            con.commit()
            logging.info('correo agregado {} {}'.format(dni,correo))

        except Exception as e:
            con.rollback()
            logging.exception(e)

        finally:
            cur.close()

    finally:
        con.close()