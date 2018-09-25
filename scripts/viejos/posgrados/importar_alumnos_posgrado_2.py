
if __name__ == '__main__':
    import psycopg2
    import sys
    import os
    import logging
    import datetime
    logging.getLogger().setLevel(logging.DEBUG)
    hdlr = logging.FileHandler('/tmp/importar_posgrado.log',encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s')
    hdlr.setFormatter(formatter)
    logging.getLogger().addHandler(hdlr)

    import csv
    import uuid

    login = {}

    h = os.environ['USERS_DB_HOST']
    pp = os.environ['USERS_DB_PORT']
    n = os.environ['USERS_DB_NAME']
    u = os.environ['USERS_DB_USER']
    p = os.environ['USERS_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = conn.cursor()
        try:

            archivo = sys.argv[1]
            with open(archivo,'r',encoding='utf-8') as f:
                cr = csv.reader(f,delimiter=',')
                for a in cr:
                    #logging.info(a)
                    nombre = a[1].strip().capitalize()
                    apellido = a[2].strip().capitalize()
                    dni = a[3].lower().strip()
                    correo = a[4].lower().strip()
                    uid = str(uuid.uuid4())
                    #logging.info('importando {} {} {}'.format(nombre, apellido, dni))
                    cur.execute('select id from usuarios where dni = %s', (dni,))

                    if cur.rowcount > 0:
                        logging.info('{},{},{},ya existe. no se lo toca'.format(nombre,apellido,dni))
                    else:
                        logging.info('{},{},{},importado'.format(nombre,apellido,dni))
                        cur.execute('insert into usuarios (id,nombre,apellido,dni) values (%s,%s,%s,%s)', (uid, nombre, apellido, dni))
                        mid = str(uuid.uuid4())
                        cur.execute('insert into mails (id,usuario_id,email,confirmado) values (%s,%s,%s,NOW())', (mid, uid, correo))
                        login[uid] = dni

            conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()


    h = os.environ['LOGIN_DB_HOST']
    pp = os.environ['LOGIN_DB_PORT']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = conn.cursor()
        try:
            for uid in login.keys():
                dni = login[uid]
                pid = str(uuid.uuid4())
                cur.execute('insert into usuario_clave (id,usuario_id,usuario,clave) values (%s,%s,%s,%s)', (pid,uid,dni,'accesounlp'))

            conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()
