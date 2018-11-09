
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
    le.addHandler(lih)

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
                    nombre = a[1].split(',')[1].strip().capitalize()
                    apellido = a[1].split(',')[0].strip().capitalize()
                    dni = a[2].lower().strip().replace('dni', '').replace('ci','').replace('pas','').replace('dnt', '')
                    uid = str(uuid.uuid4())
                    logging.info('importando {} {} {}'.format(nombre, apellido, dni))
                    cur.execute('select id from usuarios where dni = %s', (dni,))
                    if cur.rowcount <= 0:
                        li.info('{},{},{},creado'.format(dni, nombre, apellido))
                        cur.execute('insert into usuarios (id,nombre,apellido,dni,tipo) values (%s,%s,%s,%s,%s)', (uid, nombre, apellido, dni, 'ingresante'))
                    else:
                        uid = cur.fetchone()[0]
                        le.info('{},{},{},{},existente - se actualiza tipo'.format(uid, dni, nombre, apellido))
                        cur.execute('update usuarios set tipo = %s where id = %s', ('ingresante', uid))

            conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()
