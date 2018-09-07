
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
            cur2.execute('select id, email from users_migracion')
            for m in cur2.fetchall():
                print('Agregando: ')
                uid = m[0]
                print('UID: ',uid)
                correo = m[1]
                print('Correo: ',correo)
                try:
                    cur.execute("insert into mails (id, email, user_id) values (%s,%s,%s)", (str(uuid.uuid4()), correo, uid))
                    conn.commit()
                    print('--Agregado--')
                except Exception as e:
                    print(e)
                    conn.rollback()
        finally:
            conn2.close()

    finally:
        conn.close()
