

if __name__ == '__main__':

    import os
    from sqlalchemy import create_engine
    from model_utils import Base
    from users.model.entities import *

    def crear_tablas():
        #engine.execute(CreateSchema('users'))
        engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
            os.environ['USERS_DB_USER'],
            os.environ['USERS_DB_PASSWORD'],
            os.environ['USERS_DB_HOST'],
            os.environ['USERS_DB_PORT'],
            os.environ['USERS_DB_NAME']
        ), echo=True)
        Base.metadata.create_all(engine)


    crear_tablas()
