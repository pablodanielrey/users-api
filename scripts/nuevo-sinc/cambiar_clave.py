
import os
import psycopg2
import sys
import logging
logging.getLogger().setLevel(logging.DEBUG)
import uuid
import datetime

if __name__ == '__main__':


    if len(sys.argv) < 3:
        logging.info('debe ejecutar el script usando: {} dni clave'.format(sys.argv[0]))

    dni = sys.argv[1]
    clave = sys.argv[2]

    if len(clave) < 8:
        logging.info('No se permiten claves menores a 8 caracteres')



    h = os.environ['USERS_DB_HOST']
    pp = os.environ['USERS_DB_PORT']
    n = os.environ['USERS_DB_NAME']
    u = os.environ['USERS_DB_USER']
    p = os.environ['USERS_DB_PASSWORD']

    uid = None

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = con.cursor()
        try:
            cur.execute('select id,dni from usuarios where dni = %s', (dni,))
            u = cur.fetchone()
            uid = u[0]
            dni = u[1]
        finally:
            cur.close()
    finally:
        con.close()


    h = os.environ['LOGIN_DB_HOST']
    pp = os.environ['LOGIN_DB_PORT']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    ahora = datetime.datetime.now()

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = con.cursor()
        try:
            cur.execute('update usuario_clave set eliminada = %s where usuario_id = %s', (ahora, uid))
            cid = str(uuid.uuid4())
            cur.execute('insert into usuario_clave (id, usuario_id, usuario, clave, dirty) values (%s,%s,%s,%s,%s)', (cid, uid, dni, clave,True))
            logging.info('clave cambiada {} = {}'.format(dni,clave))
            con.commit()

        except Exception as e:
            con.rollback()
            logging.exception(e)

        finally:
            cur.close()

    finally:
        con.close()