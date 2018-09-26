
if __name__ == '__main__':

    h = os.environ['LOGIN_DB_HOST']
    pp = os.environ['LOGIN_DB_PORT']
    n = os.environ['LOGIN_DB_NAME']
    u = os.environ['LOGIN_DB_USER']
    p = os.environ['LOGIN_DB_PASSWORD']

    if len(sys.argv) < 3:
        logging.info('debe ejecutar el script usando: {} dni clave'.format(sys.argv[0]))

    dni = sys.argv[1]
    clave = sys.arv[2]

    if len(clave) < 8:
        logging.info('No se permiten claves menores a 8 caracteres')


    ahora = datetime.datetime.now()

    con = psycopg2.connect(dbname=n, host=h, port=pp, user=u, password=p)
    try:
        cur = conn.cursor()
        try:
            cur.execute('select usuario_id from usuario_clave where dni = %s', (dni,))
            uid = cur.fetch_one()[0]
            cur.execute('update usuario_clave set eliminada = %s where usuario = %s', (ahora, dni))
            cid = str(uuid.uuid4())
            cur.execute('insert into usuario_clave (id, usuario_id, usuario, clave, dirty) values (%s,%s,%s,%s,%s)', (cid, uid, dni, clave,True))
            con.commit()

        except Exception as e:
            con.rollback()
            logging.exception(e)

        finally:
            cur.close()

    finally:
        con.close()