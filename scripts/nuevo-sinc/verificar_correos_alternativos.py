
import os
import psycopg2
import sys
import logging
logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':

    """
        analizo quien no tiene correo alternativo confirmado
    """

    h = os.environ['USERS_OLD_DB_HOST']
    pp = os.environ['USERS_OLD_DB_PORT']
    n = os.environ['USERS_OLD_DB_NAME']
    u = os.environ['USERS_OLD_DB_USER']
    p = os.environ['USERS_OLD_DB_PASSWORD']

    usuarios = []

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = con.cursor()
        try:
            cur.execute('select id, dni, name, lastname from users where id not in (select user_id from mails where confirmado is not null and eliminado is null group by user_id)')
            for u in cur.fetchall():
                usuarios.append({
                        'id':u[0],
                        'dni':u[1],
                        'nombre':u[2],
                        'apellido':u[3]
                })
    
        except Exception as e:
            logging.exception(e)

        finally:
            cur.close()
    finally:
        con.close()    


    for u in usuarios:
        logging.info(u)