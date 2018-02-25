import psycopg2
from psycopg2.extras import DictCursor
import os
import uuid
import datetime
import logging
logging.getLogger().setLevel(logging.DEBUG)
import sys

if __name__ == '__main__':
    conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['USERS_DB_HOST'],
        os.environ['USERS_DB_USER'],
        os.environ['USERS_DB_PASSWORD'],
        os.environ['USERS_DB_NAME']
    ))
    cur = conn.cursor()
    try:
        conn2 = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
            os.environ['OLD_USERS_DB_HOST'],
            os.environ['OLD_USERS_DB_USER'],
            os.environ['OLD_USERS_DB_PASSWORD'],
            os.environ['OLD_USERS_DB_NAME']
        ))
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            ''' sinc usuarios '''
            cur2.execute('select id, student_number from students.users')
            for u in cur2.fetchall():
                #logging.info('sincronizando : {}'.format(u))
                try:
                    cur.execute('update users set legajo=%(student_number)s where id=%(id)s', u)

                except Exception as e:
                    logging.exception(e)
                    conn.rollback()
            conn2.commit()

        finally:
            cur2.close()
            conn2.close()

    finally:
        cur.close()
        conn.close()
