if __name__ == '__main__':
    import psycopg2
    import sys
    import os
    import datetime
    import uuid
    
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
            cur2 = conn2.cursor()
            try:
                cur2.execute('select id, dni, nombre, apellido, genero, nacimiento, ciudad, pais, direccion, tipo, avatar from users where dirty= %s', (True,))
                for u in cur2.fetchall():
                    cur.execute('select dni from usuarios where dni = %s', (u.dni,))
                    if cur.rowcount > 0:
                        print('El usuario {},{},{}, ya existe. no se lo toca'.format(u.nombre,u.apellido,u.dni))
                    else:
                        cur.execute('insert into usuarios (id, dni, nombre, apellido, genero, nacimiento, ciudad, pais, direccion, tipo, avatar) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (u.id, u.dni, u.nombre, u.apellido, u.genero, u.nacimiento, u.ciudad, u.pais, u.direccion, u.tipo, u.avatar))
                        
                        ''' sinc correos '''
                        ''' elimino los correos de la base vieja para este usuario'''
                        cur.execute('select id from mails where usuario_id = %s and eliminado is not null', (u.id,))
                        if cur.rowcount >0:
                            for m in cur.fetchall():
                                cur.execute('delete from mails where id in %s', (m.id,))
                        
                        ''' actualizo los correos '''
                        cur2.execute('select * from mails where eliminado is null and confirmado is not null and usuario_id %s)', (u.id,))
                        for m in cur2.fetchall():
                            cur.execute('insert into mails (id, user_id, email, confirmado, hash, creado) values (%s,%s,%s,%s,%s,%s)', (m.id, u.id, m.mail, m.confirmado, m.hash, m.creado))
                    cur2.execute('update usuarios set dirty = %s where usuario = %s', (False,u.dni)) ')
                conn.commit()
            except:
                conn.rollback()
            finally:
                conn2.close()
    finally:
        conn.close()