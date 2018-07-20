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
    sq = "update users set legajo = %s where dni = %s"
    try:
        with open(sys.argv[1]) as f:
            for l in f:
                u = l[0:l.find('|')].strip()
                p = l[l.find('|')+1:].strip()
                print(u)

                try:
                    cur.execute(sq, (p,u))
                    conn.commit()
                except Exception as e:
                    logging.exception(e)
    finally:
        conn.close()