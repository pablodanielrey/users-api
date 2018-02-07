import psycopg2
from psycopg2.extras import DictCursor
import os
import uuid
import datetime
import logging
logging.getLogger().setLevel(logging.DEBUG)

"""
    hay que sincronizar:

                    Table "profile.users"
     Column     |            Type             |   Modifiers
----------------+-----------------------------+---------------
 id             | character varying           | not null
 dni            | character varying           | not null
 name           | character varying           |
 lastname       | character varying           |
 genre          | character varying           |
 birthdate      | date                        |
 city           | character varying           |
 country        | character varying           |
 address        | character varying           |
 residence_city | character varying           |
 created        | timestamp with time zone    | default now()
 version        | bigint                      | default 0
 photo          | character varying           |
 type           | character varying           |
 google         | boolean                     | default false
 gender         | character varying           |
 creado         | timestamp without time zone | default now()
 actualizado    | timestamp without time zone |
 avatar         | character varying           |


                    Table "profile.telephones"
   Column    |            Type             |   Modifiers
-------------+-----------------------------+---------------
 id          | character varying           | not null
 user_id     | character varying           | not null
 number      | character varying           | not null
 type        | character varying           |
 actualizado | timestamp without time zone |
 creado      | timestamp without time zone | default now()

                          Table "profile.mails"
      Column      |            Type             |       Modifiers
------------------+-----------------------------+------------------------
 id               | character varying           | not null
 user_id          | character varying           | not null
 email            | character varying           | not null
 confirmed        | boolean                     | not null default false
 hash             | character varying           |
 created          | timestamp without time zone | default now()
 creado           | timestamp without time zone | default now()
 actualizado      | timestamp without time zone |
 eliminado        | timestamp without time zone |
 fecha_confirmado | timestamp without time zone |


              Table "credentials.user_password"
     Column     |            Type             |   Modifiers
----------------+-----------------------------+---------------
 id             | character varying           | not null
 user_id        | character varying           | not null
 username       | character varying           | not null
 password       | character varying           | not null
 updated        | timestamp without time zone | default now()
 creado         | timestamp without time zone | default now()
 actualizado    | timestamp without time zone |
 expiracion     | timestamp without time zone |
 eliminada      | timestamp without time zone |
 debe_cambiarla | boolean                     | default false
 autogenerada   | boolean                     | default false


hacia estas tablas:

users=# \dt
              List of relations
 Schema |        Name        | Type  | Owner
--------+--------------------+-------+-------
 public | mails              | table | users
 public | telephones         | table | users
 public | user_password      | table | users
 public | users              | table | users


"""

if __name__ == '__main__':
    import sys

    conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['OLD_USERS_DB_HOST'],
        os.environ['OLD_USERS_DB_USER'],
        os.environ['OLD_USERS_DB_PASSWORD'],
        os.environ['OLD_USERS_DB_NAME']
    ))
    cur = conn.cursor()
    try:
        conn2 = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
            os.environ['USERS_DB_HOST'],
            os.environ['USERS_DB_USER'],
            os.environ['USERS_DB_PASSWORD'],
            os.environ['USERS_DB_NAME']
        ))
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            ''' sinc usuarios '''
            # cur2.execute('select max(u.actualizado), max(u2.creado) from users u inner join users u2 on u.id = u2.id')


            cur2.execute('select id, dni, name, lastname, actualizado, creado from users')
            for u in cur2.fetchall():
                sys.stdout.write('.')
                sys.stdout.flush()
                try:
                    if u['actualizado']:
                        cur.execute('select id from profile.users where dni = %(dni)s and sincronizado_1 < %(actualizado)s', u)
                    else:
                        cur.execute('select id from profile.users where dni = %(dni)s and sincronizado_1 < %(creado)s', u)
                    if cur.rowcount > 0:
                        logging.info('sincronizando : {}'.format(u))
                        cur.execute('update profile.users set dni=%(dni)s, name=%(name)s, lastname=%(lastname)s, sincronizado_1=NOW() where id=%(id)s', u)
                        conn.commit()

                except Exception as e:
                    logging.exception(e)
                    conn.rollback()

            ''' sinc claves '''

            ''' chequeo primero si hace falta la sincronizacion '''

            """
            cur2.execute('select max(u.actualizado), max(u2.creado) from user_password u inner join user_password u2 on u.id = u2.id;')
            m = cur2.fetchone()
            fecha = m[0] if m[0] > m[1] else m[1]
            logging.debug('cheqeuando a ver si existe sincronizacion que sea menor que {}'.format(fecha))
            cur.execute('select id from profile.users where sincronizado_1 < %s', (fecha,))
            if cur.rowcount > 0:
                ''' existe al menos 1 que necesita ser sincronizado '''
            """

            cur2.execute('select id, user_id, username, password, creado, actualizado from user_password where eliminada is null')
            for u in cur2.fetchall():
                sys.stdout.write('.');
                sys.stdout.flush()
                try:
                    if u['actualizado']:
                        cur.execute('select id from credentials.user_password where username = %(username)s and sincronizado_1 < %(actualizado)s', u)
                    else:
                        cur.execute('select id from credentials.user_password where username = %(username)s and sincronizado_1 < %(creado)s', u)
                    if cur.rowcount > 0:
                        logging.debug('.')
                        logging.debug('actualizando clave : {}'.format(u))
                        cur.execute('update credentials.user_password set password = %(password)s, sincronizado_1=NOW() where id = %(id)s', u)
                        conn.commit()

                except Exception as e:
                    logging.exception(e)
                    conn.rollback()


            ''' sinc correos '''
            ''' elimino los correos em la base vieja '''
            cur2.execute('select id from mails where eliminado is not null')
            try:
                mids = [m[0] for m in cur2.fetchall()]
                logging.info('correos que se van a eliminar {}'.format(mids))
                cur.execute('delete from profile.mails where id in %s', (tuple(mids),))
                conn.commit()
            except Exception as e:
                logging.exception(e)
                conn.rollback()

            ''' actualizo los correos '''
            ''' chequeo primero si hace falta la sincronizacion '''

            cur2.execute('select max(actualizado), max(creado) from mails')
            m = cur2.fetchone()
            fecha = m[0] if m[0] > m[1] else m[1]
            logging.debug('cheqeuando a ver si existe sincronizacion que sea menor que {}'.format(fecha))
            cur.execute('select id from profile.mails where sincronizado_1 < %s', (fecha,))
            if cur.rowcount > 0:
                ''' existe al menos 1 que necesita ser sincronizado '''
                logging.info("existe al menos 1 que necesita ser sincronizado")
                cur2.execute('select * from mails where eliminado is null')
                for m in cur2.fetchall():
                    logging.info('procesando correo {}'.format(m['email']))
                    try:
                        cur.execute('select id, sincronizado_1 from profile.mails where id = %(id)s', m)

                        if cur.rowcount > 0:
                            c = cur.fetchone()
                            if (m['actualizado'] and c[1] < m["actualizado"]) or (c[1] < m["creado"]):
                                logging.info('actualizando mail {}'.format(m['email']))
                                cur.execute('update profile.mails set actualizado = %(actualizado)s , sincronizado_1=NOW(), email = %(email)s, fecha_confirmado = %(confirmado)s, confirmed = %(confirmado)s is not null where id = %(id)s',m)
                            else:
                                cur.execute('update profile.mails set sincronizado_1=NOW() where id = %(id)s',m)
                        else:
                            logging.info('creando mail {}'.format(m))
                            cur.execute("""insert into profile.mails (id, user_id, email, confirmed, hash, creado, actualizado, fecha_confirmado, sincronizado_1) \
                                        values(%(id)s,%(user_id)s,%(email)s,%(confirmado)s is not null,%(hash)s,%(creado)s,%(actualizado)s,%(confirmado)s,NOW())""", m)
                        conn.commit()
                    except Exception as e:
                        logging.exception(e)
                        conn.rollback()

        finally:
            cur2.close()
            conn2.close()

    finally:
        cur.close()
        conn.close()
