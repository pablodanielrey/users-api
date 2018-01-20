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
    conn = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['USERS_DB_HOST'],
        os.environ['USERS_DB_USER'],
        os.environ['USERS_DB_PASSWORD'],
        os.environ['USERS_DB_NAME']
    ))
    cur = conn.cursor()
    try:
        conn2 = psycopg2.connect("host='{}' user='{}' password='{}' dbname={}".format(
            os.environ['OLD_USERS_DB_HOST'],
            os.environ['OLD_USERS_DB_USER'],
            os.environ['OLD_USERS_DB_PASSWORD'],
            os.environ['OLD_USERS_DB_NAME']
        ))
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            ''' sinc usuarios '''
            cur2.execute('select id, dni, name, lastname from profile.users')
            for u in cur2.fetchall():
                logging.info('sincronizando : {}'.format(u))
                try:
                    cur.execute('insert into users (id, dni, name, lastname) values (%(id)s,%(dni)s,%(name)s,%(lastname)s)', u)
                    conn.commit()
                except Exception as e:
                    logging.exception(e)
                    conn.rollback()

            ''' sinc claves '''
            cur2.execute('select id, user_id, username, password from credentials.user_password')
            for u in cur2.fetchall():
                if u['username'] == u['password']:
                    u['password'] = str(uuid.uuid4())
                    logging.info('reemplazando la clave ya que es igual al nombre de usuario')
                logging.info('sincronizando : {}'.format(u))
                try:
                    cur.execute('insert into user_password (id, user_id, username, password) values (%(id)s,%(user_id)s,%(username)s,%(password)s)', u)
                    conn.commit()
                except Exception as e:
                    logging.exception(e)
                    conn.rollback()

            ''' sinc correos '''
            cur2.execute('select id, user_id, email, fecha_confirmado, eliminado, confirmed from profile.mails where eliminado is Null')
            for u in cur2.fetchall():
                if not u['fecha_confirmado'] and not u['confirmed']:
                    continue
                if not u['fecha_confirmado'] and u['confirmed']:
                    u['fecha_confirmado'] = datetime.datetime.now()

                logging.info('sincronizando : {}'.format(u))
                try:
                    cur.execute('insert into mails (id, user_id, email, confirmado, eliminado) values (%(id)s,%(user_id)s,%(email)s,%(fecha_confirmado)s,%(eliminado)s)', u)
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
