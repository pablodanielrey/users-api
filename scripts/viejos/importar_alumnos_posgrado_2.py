
if __name__ == '__main__':
    import psycopg2
    import sys
    import os
    import logging
    import datetime
    logging.getLogger().setLevel(logging.DEBUG)
    hdlr = logging.FileHandler('/tmp/importar_posgrado.log')
    formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s')
    hdlr.setFormatter(formatter)
    logging.getLogger().addHandler(hdlr)

    import csv
    import uuid

    login = {}

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

            #conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()


    h = os.environ['LOGIN_DB_HOST']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, user=u, password=p)
    try:
        cur = conn.cursor()
        try:

            archivo = sys.argv[1]
            for uid in login.keys():
                dni = login[uid]
                pid = str(uuid.uuid4())
                cur.execute('insert into user_password (id,user_id,username,password,debe_cambiarla) values (%s,%s,%s,%s,false)', (pid,uid,dni,'accesounlp'))

            #conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()
