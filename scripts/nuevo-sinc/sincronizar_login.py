
if __name__ == '__main__':

    claves = []

    h = os.environ['LOGIN_DB_HOST']
    pp = os.environ['LOGIN_DB_PORT']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:

        cur = conn.cursor()
        try:
            cur.execute('select dni, clave from usuario_clave where dirty = %s', (True,))
            for l in cur.fetchall():
                logging.info('agregando {} para sincronizar'.format(l[0]))
                claves.append({
                    'dni':l[0],
                    'clave':l[1],
                    'actualizado':False
                }) 

        finally:
            cur.close()

    finally:
        conn.close()


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
                dni = u['dni']
                clave = u['clave']
                logging.info('{} - clave'.format(dni))
                cur.execute('update user_password set password = %s, actualizado = NOW() where username = %s', (dni,clave))
                con.commit()
    
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
                        cur.execute('update usuario_clave set dirty = %s where dni = %s', (False,dni))
                        conn.commit()
                except Exception as e:
                    logging.exception(e)
                    conn.rollback()

        finally:
            cur.close()

    finally:
        conn.close()
