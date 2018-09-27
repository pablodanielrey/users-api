
import os
import psycopg2
import sys
import logging
logging.getLogger().setLevel(logging.DEBUG)
import uuid

if __name__ == '__main__':

    claves = []

    h = os.environ['LOGIN_DB_HOST']
    pp = os.environ['LOGIN_DB_PORT']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    """
        veo quien necesita actualizacion
    """

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:

        cur = conn.cursor()
        try:
            cur.execute('select usuario_id, usuario, clave from usuario_clave where dirty = %s and eliminada is null', (True,))
            for l in cur.fetchall():
                logging.info('agregando {} para sincronizar'.format(l[0]))
                claves.append({
                    'uid':l[0],
                    'dni':l[1],
                    'clave':l[2],
                    'actualizado':False
                }) 

        finally:
            cur.close()

    finally:
        conn.close()


    """
        actualizo las claves
    """

    h = os.environ['USERS_OLD_DB_HOST']
    pp = os.environ['USERS_OLD_DB_PORT']
    n = os.environ['USERS_OLD_DB_NAME']
    u = os.environ['USERS_OLD_DB_USER']
    p = os.environ['USERS_OLD_DB_PASSWORD']

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = con.cursor()
        try:
            for u in claves:
                try:
                    dni = u['dni']
                    clave = u['clave']
                    logging.info('{} - clave'.format(dni))
                    cur.execute('update user_password set password = %s, actualizado = NOW() where username = %s', (clave, dni))
                    if cur.rowcount <= 0:
                        cid = str(uuid.uuid4())
                        uid = u['uid']
                        cur.execute('insert into user_password (id, user_id, username, password) values (%s,%s,%s,%s)',(cid, uid, dni, clave))
                        logging.info('insertado : {} - clave'.format(dni))
                    con.commit()
                    u['actualizado'] = True
    
                except Exception as e:
                    u['actualizado'] = False
                    con.rollback()
                    logging.exception(e)

        finally:
            cur.close()
    finally:
        con.close()    


    """
        actualizo los dirty
    """

    h = os.environ['LOGIN_DB_HOST']
    pp = os.environ['LOGIN_DB_PORT']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:

        cur = conn.cursor()
        try:
            for u in claves:
                try:
                    if u['actualizado']:
                        dni = u['dni']
                        logging.info('{} - dirty = False'.format(dni))
                        cur.execute('update usuario_clave set dirty = %s where usuario = %s', (False,dni))
                        conn.commit()
                except Exception as e:
                    logging.exception(e)
                    conn.rollback()

        finally:
            cur.close()

    finally:
        conn.close()
