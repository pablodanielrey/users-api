
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
                    nombe = a[1].split(',')[0].strip().capitalize()
                    apellido = a[1].split(',')[1].strip().capitalize()
                    dni = a[3].lower().strip()
                    uid = str(uuid.uuid4())
                    logging.info('importando {} {} {}'.format(nombre, apellido, dni))
                    cur.execute('select id from users where dni = %s', (dni,))
                    if cur.rowcount <= 0:
                        logging.info('agregando {}'.format(dni))
                        cur.execute('insert into users (id,name,lastname,dni) values (%s,%s,%s,%s)', (uid, nombre, apellido, dni))

            conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()
