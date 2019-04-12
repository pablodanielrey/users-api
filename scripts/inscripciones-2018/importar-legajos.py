
if __name__ == '__main__':
    import psycopg2
    import sys
    import os
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    import csv
    import uuid

    li = logging.getLogger('insertado')
    lih = logging.FileHandler('creado.log')
    li.addHandler(lih)

    le = logging.getLogger('existente')
    leh = logging.FileHandler('existente.log')
    le.addHandler(leh)

    h = os.environ['USERS_DB_HOST']
    pp = os.environ['USERS_DB_PORT']
    n = os.environ['USERS_DB_NAME']
    u = os.environ['USERS_DB_USER']
    p = os.environ['USERS_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = conn.cursor()
        try:
            header = True
            archivo = sys.argv[1]
            with open(archivo,'r') as f:
                cr = csv.reader(f,delimiter=';')
                for a in cr:
                    if header:
                        header = False
                        continue
                    logging.info(a)
                    legajo = a[0].replace(' ','').lower()
                    dni = a[1].replace(' ','').lower()
                    uid = str(uuid.uuid4())
                    logging.info('buscando {}'.format(dni))
                    cur.execute('select id from usuarios where dni = %s or legajo = %s', (dni,legajo))
                    if cur.rowcount > 0:
                        uid = cur.fetchone()[0]
                        le.info('{},existente - se actualiza legajo'.format(dni))
                        cur.execute('update usuarios set legajo = %s where id = %s', (legajo,uid))
                    else:
                        li.info('{} no existe'.format(dni))

            conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()
