
if __name__ == '__main__':
    import psycopg2
    import sys
    import os
    import logging
    import datetime
    logging.getLogger().setLevel(logging.DEBUG)
    hdlr = logging.FileHandler('/tmp/importar_posgrado_base1.log',encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s')
    hdlr.setFormatter(formatter)
    logging.getLogger().addHandler(hdlr)

    import csv
    import uuid

    h = os.environ['USERS_OLD_DB_HOST']
    pp = os.environ['USERS_OLD_DB_PORT']
    n = os.environ['USERS_OLD_DB_NAME']
    u = os.environ['USERS_OLD_DB_USER']
    p = os.environ['USERS_OLD_DB_PASSWORD']

    conn = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = conn.cursor()
        try:

            archivo = sys.argv[1]
            with open(archivo,'r', encoding='utf-8') as f:
                cr = csv.reader(f,delimiter=',')
                for a in cr:
                    #logging.info(a)
                    nombre = a[1].strip().capitalize()
                    apellido = a[2].strip().capitalize()
                    dni = a[3].lower().strip()
                    correo = a[4].lower().strip()
                    uid = str(uuid.uuid4())
                    #logging.info('importando {} {} {}'.format(nombre, apellido, dni))
                    cur.execute('select id, name, lastname from users where dni = %s', (dni,))

                    if cur.rowcount > 0:
                        logging.info('{},{},{},ya existe. no se lo toca'.format(nombre,apellido,dni))
                    else:
                        logging.info('{},{},{},{},importado'.format(nombre,apellido,dni,correo))
                        cur.execute('insert into users (id,name,lastname,dni) values (%s,%s,%s,%s)', (uid, nombre, apellido, dni))
                        mid = str(uuid.uuid4())
                        cur.execute('insert into mails (id,user_id,email,confirmado) values (%s,%s,%s,NOW())', (mid, uid, correo))
                        pid = str(uuid.uuid4())
                        cur.execute('insert into user_password (id,user_id,username,password,debe_cambiarla) values (%s,%s,%s,%s,false)', (pid,uid,dni,'accesounlp'))

            conn.commit()

        except Exception as e:
            logging.exception(e)

    finally:
        conn.close()
