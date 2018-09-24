
if __name__ == '__main__':

    import sys
    from sqlalchemy import  or_
    from users.model.entities import Usuario, Mail, Telefono
    from users.model import obtener_session

    import logging
    logging.getLogger().setLevel(logging.INFO)
    import os
    import psycopg2

    with obtener_session() as s:

        con = psycopg2.connect("host={} port={} dbname={} user={} password={}".format(
            os.environ['OLD_USERS_DB_HOST'],
            os.environ['OLD_USERS_DB_PORT'],
            os.environ['OLD_USERS_DB_NAME'],
            os.environ['OLD_USERS_DB_USER'],
            os.environ['OLD_USERS_DB_PASSWORD']))
        cur = con.cursor()
        cur.execute('select id, creado, actualizado, dni, name, lastname, legajo from users')
        for c in cur:
            uid = c[0]
            creado = c[1]
            actualizado = c[2]
            dni = c[3].replace(' ','').replace('.','').lower()
            cu = s.query(Usuario).filter(Usuario.id == uid).one_or_none()
            if not cu:
                try:
                    print('creando {}'.format(dni))
                    uc = Usuario()
                    uc.id = uid
                    uc.creado = creado
                    uc.actualizado = actualizado
                    uc.dni = dni
                    uc.nombre = c[4]
                    uc.apellido = c[5]
                    uc.legajo = c[6]
                    s.add(uc)
                    s.commit()
                except Exception as e:
                    logging.exception(e)
                    s.rollback()

        cur.execute('select id, creado, actualizado, email, user_id, eliminado, confirmado from mails')
        for c in cur:
            mid = c[0]
            creado = c[1]
            actualizado = c[2]
            email = c[3].replace(' ','').lower()
            if not s.query(Mail).filter(Mail.id == mid).one_or_none():
                try:
                    print('creando {}'.format(email))
                    m = Mail()
                    m.id = mid
                    m.creado = creado
                    m.actualizado = actualizado
                    m.email = email
                    m.usuario_id = c[4]
                    m.eliminado = c[5]
                    m.confirmado = c[6]
                    s.add(m)
                    s.commit()
                except Exception as e:
                    logging.exception(e)
                    s.rollback()


