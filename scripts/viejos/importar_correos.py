import psycopg2
from psycopg2.extras import DictCursor
import os
import uuid
import datetime
import logging
logging.getLogger().setLevel(logging.DEBUG)
import sys

if __name__ == '__main__':

    conn = psycopg2.connect("host='{}' port='{}' user='{}' password='{}' dbname={}".format(
        os.environ['USERS_DB_HOST'],
        os.environ['USERS_DB_PORT'],
        os.environ['USERS_DB_USER'],
        os.environ['USERS_DB_PASSWORD'],
        os.environ['USERS_DB_NAME']
    ))
    cur = conn.cursor()

    cur.execute('select u.dni from users u where u.dni not in (select u.dni from mails m, users u where u.id = m.user_id and m.confirmado is not null)')
    noconf = [c[0] for c in cur]

    sq2 = "select id from users where dni = %s"
    sq = "insert into mails (id,user_id,email,confirmado) values (%s,%s,%s,NOW())"
    try:
        cuenta = 0
        with open(sys.argv[1]) as f:
            for l in f:
                d = l[0:l.find('|')].strip()
                c = l[l.find('|')+1:].strip()
                print(d)
                print(c)

                try:
                    if d in noconf:
                        cuenta = cuenta + 1
                        cur.execute(sq2, (d,))
                        if cur:
                            uid = cur.fetchone()[0]
                            cur.execute(sq, (str(uuid.uuid4()),uid,c))
                            conn.commit()
                except Exception as e:
                    logging.exception(e)

        print('cantidad: {}'.format(cuenta))
    finally:
        conn.close()