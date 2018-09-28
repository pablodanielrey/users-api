import os
import psycopg2
import logging; logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':

    h2 = os.environ['USERS_DB_HOST']
    pp2 = os.environ['USERS_DB_PORT']
    n2 = os.environ['USERS_DB_NAME']
    u2 = os.environ['USERS_DB_USER']
    p2 = os.environ['USERS_DB_PASSWORD']
    
    usuarios = None
    con = psycopg2.connect(dbname=n2, host=h2, port=pp2, user=u2, password=p2)
    try:
        cur = con.cursor()
        try:
            cur.execute('select id from usuarios')
            u = [u[0] for u in cur]
            usuarios = tuple(u)
        finally:
            cur.close()
    finally:
        con.close()

    h = os.environ['LOGIN_DB_HOST']
    pp = os.environ['LOGIN_DB_PORT']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = con.cursor()
        try:
            cur.execute('select id,usuario,clave from usuario_clave where usuario_id not in %s', (usuarios,))
            for i in cur.fetchall():
                logging.info('{},{},{}'.format(i[0],i[1],i[2]))
                cur.execute('delete from usuario_clave where id = %s', (i[0],))
                con.commit()
        finally:
            cur.close()
    finally:
        con.close()
