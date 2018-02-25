import psycopg2
from psycopg2.extras import DictCursor
import os
import uuid
import datetime
import logging

hdr = logging.FileHandler('/tmp/base.sync.log')
logging.getLogger().addHandler(hdr)
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


dcsys=# \d students.users
             Table "students.users"
     Column     |       Type        | Modifiers
----------------+-------------------+-----------
 id             | character varying | not null
 student_number | character varying |
 condition      | character varying |
Indexes:
    "users_pkey" PRIMARY KEY, btree (id)
    "users_student_number_key" UNIQUE CONSTRAINT, btree (student_number)
Foreign-key constraints:
    "users_id_fkey" FOREIGN KEY (id) REFERENCES profile.users(id)

dcsys=#



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
from psycopg2.extras import LoggingConnection

if __name__ == '__main__':
    import sys

    dsn = "host='{}' user='{}' password='{}' dbname={}".format(
        os.environ['OLD_USERS_DB_HOST'],
        os.environ['OLD_USERS_DB_USER'],
        os.environ['OLD_USERS_DB_PASSWORD'],
        os.environ['OLD_USERS_DB_NAME']
    )
    conn = psycopg2.connect(dsn)
    logfile = open('/tmp/db.log', 'a')
    conn = LoggingConnection(dsn)
    conn.initialize(logfile)


    cur = conn.cursor()
    try:
        dsn2 = "host='{}' user='{}' password='{}' dbname={}".format(
            os.environ['USERS_DB_HOST'],
            os.environ['USERS_DB_USER'],
            os.environ['USERS_DB_PASSWORD'],
            os.environ['USERS_DB_NAME']
        )
        conn2 = psycopg2.connect(dsn2)
        logfile2 = open('/tmp/db_new.log', 'a')
        conn2 = LoggingConnection(dsn2)
        conn2.initialize(logfile2)
        cur2 = conn2.cursor(cursor_factory=DictCursor)
        try:
            ''' sinc usuarios '''
            cur2.execute('select max(fecha) from scripts')
            if cur2.rowcount > 0:
                fecha = cur2.fetchone()[0] - datetime.timedelta(hours=3)
            if not fecha:
                fecha = datetime.datetime.now() - datetime.timedelta(days=365)
            logging.debug('fecha {}'.format(fecha))
            error = False

            cur2.execute('select id, dni, name, lastname, legajo, actualizado, creado from users where actualizado > %s or creado > %s', (fecha, fecha))
            for u in cur2.fetchall():
                logging.info('sincronizando : {}'.format(u))
                #sys.stdout.write('.')
                #sys.stdout.flush()
                cur.execute('update profile.users set dni=%(dni)s, name=%(name)s, lastname=%(lastname)s, sincronizado_1=NOW() where id=%(id)s', u)
                if cur.rowcount <= 0:
                    cur.execute('insert into profile.users (id,dni,name,lastname,sincronizado_1) values (%(id)s, %(dni)s, %(name)s, %(lastname)s, NOW())', u)
                cur.execute('update students.users set student_number=%(legajo)s where id=%(id)s', u)
                if cur.rowcount <= 0:
                    cur.execute('insert into student.users (id,legajo) values (%(id)s, %(legajo)s)', u)


            conn.commit()

            ''' sinc claves '''
            cur2.execute('select id, user_id, username, password, creado, actualizado from user_password where actualizado > %s or creado > %s', (fecha, fecha))
            for u in cur2.fetchall():
                logging.debug('actualizando clave : {}'.format(u))
                #sys.stdout.write('.')
                #sys.stdout.flush()
                cur.execute('update credentials.user_password set password = %(password)s, sincronizado_1=NOW() where id = %(id)s', u)
                if cur.rowcount <= 0:
                    cur.execute('insert into credentials.user_password (id, user_id, username, password, sincronizado_1) values (%(id)s, %(user_id)s, %(username)s, %(password)s, NOW())', u)
            conn.commit()


            ''' sinc correos '''
            ''' elimino los correos em la base vieja '''
            cur2.execute('select id from mails where eliminado is not null')
            mids = [m[0] for m in cur2.fetchall()]
            logging.info('correos que se van a eliminar {}'.format(mids))
            cur.execute('delete from profile.mails where id in %s', (tuple(mids),))
            logging.info(cur.rowcount)
            conn.commit()

            ''' actualizo los correos '''
            logging.info(' =========== actualizo los correos ======================')
            cur2.execute('select * from mails where eliminado is null and (actualizado > %s or creado > %s)', (fecha, fecha))
            for m in cur2.fetchall():
                cur.execute('select id from profile.mails where id = %(id)s', m)
                if cur.rowcount > 0:
                    logging.info('actualizando mail {}'.format(m))
                    #sys.stdout.write('.')
                    #sys.stdout.flush()
                    cur.execute('update profile.mails set actualizado = %(actualizado)s , sincronizado_1=NOW(), email = %(email)s, fecha_confirmado = %(confirmado)s, confirmed = %(confirmado)s is not null where id = %(id)s',m)
                else:
                    logging.info('insertando correo {}'.format(m))
                    #sys.stdout.write('.')
                    #sys.stdout.flush()
                    cur.execute("""insert into profile.mails (id, user_id, email, confirmed, hash, creado, actualizado, fecha_confirmado, sincronizado_1) \
                                values(%(id)s,%(user_id)s,%(email)s,%(confirmado)s is not null,%(hash)s,%(creado)s,%(actualizado)s,%(confirmado)s,NOW())""", m)
            conn.commit()


            logging.debug('escribiendo fecha de sincronizacion {}'.format(fecha))
            cur2.execute('insert into scripts (id, fecha) values (%s,%s)', (str(uuid.uuid4()),datetime.datetime.now()))
            conn2.commit()

        except Exception as e:
            logging.exception(e)

        finally:
            cur2.close()
            conn2.close()

    finally:
        cur.close()
        conn.close()
