
import psycopg2
from psycopg2.extras import DictCursor
import os
import sys
import uuid

if __name__ == '__main__':
    conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['USERS_DB_HOST'],
        os.environ['USERS_DB_USER'],
        os.environ['USERS_DB_PASSWORD'],
        os.environ['USERS_DB_NAME']
    ))
    cur = conn.cursor()
    try:
        host = sys.argv[1]
        db = sys.argv[2]
        user = sys.argv[3]
        passw = sys.argv[4]

        conn2 = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(host, user, passw, db))
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            cur2.execute('select id, dni, name, lastname, telephone, gender, country, city, notes, email, upassword, direccion from users_migracion')
            for m in cur2.fetchall():
                cur.execute('select 1 from users where id = %s', (m[0],))
                if cur.rowcount <= 0:
                    print('agregando')
                    uid = m[0]
                    dni = m[1]
                    nombre = m[2]
                    apellido = m[3]
                    telefono = m[4]
                    genero = m[5]
                    pais = m[6]
                    ciudad = m[7]
                    correo = m[9]
                    c = m[10]
                    direccion = m[11]
                    for i in range(1,10):
                        try:
                            cur.execute("insert into users (id, dni, name, lastname, gender, country, city, address) values (%s,%s,%s,%s,%s,%s,%s,%s)", (uid, dni, nombre, apellido, genero, pais, ciudad, direccion))
                            cur.execute("insert into telephones (id,number,user_id) values (%s,%s,%s)", (str(uuid.uuid4()), telefono, uid))
                            conn.commit()
                            print('agregado')
                            break
                        except Exception as e:
                            print(e)
                            conn.rollback()
                            dni = '{}_{}'.format(dni,i)
            

        finally:
            conn2.close()

    finally:
        conn.close()
