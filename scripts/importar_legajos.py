
if __name__ == '__main__':
    import psycopg2
    import sys
    import os
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    import csv
    import uuid

    h = os.environ['USERS_DB_HOST']
    n = os.environ['USERS_DB_NAME']
    u = os.environ['USERS_DB_USER']
    p = os.environ['USERS_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, user=u, password=p)
    try:
        cur = conn.cursor()
        try:

            archivo = sys.argv[1]
            with open(archivo,'r') as f:
                cr = csv.reader(f,delimiter=',')
                for a in cr:
                    logging.info(a)
                    dni = a[0].strip()
                    legajo = a[1].strip()
                    if not legajo or len(legajo) < 3:
                        continue
                    logging.info('importando {}'.format(dni, legajo))
                    cur.execute('select id from users where dni = %s', (dni,))
                    if cur.rowcount > 0:
                        u = cur.fetchone()
                        uid = u[0]
                        logging.info('actualizando {}'.format(uid))
                        cur.execute('update users set legajo = %s where id = %s', (legajo, uid))

            conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()
