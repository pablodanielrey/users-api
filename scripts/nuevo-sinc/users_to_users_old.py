if __name__ == '__main__':
    import psycopg2
    import sys
    import os
    import datetime
    import uuid
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    h = os.environ['USERS_OLD_DB_HOST']
    pp = os.environ['USERS_OLD_DB_PORT']
    n = os.environ['USERS_OLD_DB_NAME']
    u = os.environ['USERS_OLD_DB_USER']
    p = os.environ['USERS_OLD_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = conn.cursor()
        try:
            h2 = os.environ['USERS_DB_HOST']
            pp2 = os.environ['USERS_DB_PORT']
            n2 = os.environ['USERS_DB_NAME']
            u2 = os.environ['USERS_DB_USER']
            p2 = os.environ['USERS_DB_PASSWORD']
            
            conn2 = psycopg2.connect(dbname=n2, host=h2, port=pp2, user=u2, password=p2)
            try:
                cur2 = conn2.cursor()
                try:
                    cur2.execute('select id, dni, nombre, apellido, genero, nacimiento, ciudad, pais, direccion, tipo, avatar from users where dirty= %s', (True,))
                    for u in cur2.fetchall():
                        uid = u[0]
                        dni = u[1]
                        nombre = u[2]
                        app = u[3]
                        gen = u[4]
                        nac = u[5]
                        ciu = u[6]
                        pa = u[7]
                        dire = u[8]
                        tipo = u[9]
                        av = u[10]
                        cur.execute('select dni from usuarios where dni = %s', (dni,))

                        try:

                            if cur.rowcount > 0:
                                logging.info('{},{},{},existe - se actualiza'.format(nombre,apellido,dni))
                                cur.execute('update users set name = %s, lastname = %s, gender = %s, birthdate = %s, city = %s, country = %s, address = %s, type = %s, avatar = %s',
                                                            (nombre,app,gen,nac,ciu,pa,dire,tipo,av))
                            else:
                                logging.info('{},{},{},no existe - se inserta'.format(nombre,apellido,dni))
                                cur.execute('insert into users (id, dni, name, lastname, gender, birthdate, city, country, address, type, avatar) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', 
                                                            (uid, dni, nombre, app, gen, nac, ciu, pa, dire, tipo, av))
                                
                            ''' sinc correos '''
                            ''' elimino los correos de la base vieja para este usuario'''
                            cur.execute('delete from mails where usuario_id = %s',(uid,))
                        
                            ''' actualizo los correos '''
                            cur2.execute('select id, email from mails where eliminado is null and confirmado is not null and usuario_id = %s)', (uid,))
                            for m in cur2.fetchall():
                                mid = m[0]
                                email = m[1]
                                logging.info('insertando correo {} {} {} {}'.format(dni.nombre,app,email))
                                cur.execute('insert into mails (id, user_id, email, confirmado) values (%s,%s,%s,NOW())', (mid, uid, email))

                            #conn.commit()

                            try:
                                cur2.execute('update usuarios set dirty = %s where dni = %s', (False,dni))
                                #conn2.commit()

                            except Exception as e2:
                                conn2.rollback()
                                logging.exception(e2)

                        except Exception as e1:
                            conn.rollback()
                            loggin.exception(e1)

                finally:
                    cur2.close()

            finally:
                conn2.close()

        finally:
            cur.close()

    finally:
        conn.close()