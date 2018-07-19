
if __name__ == '__main__':
    import sys

    u = {
        'dni': sys.argv[1],
        'nombre': sys.argv[2],
        'apellido': sys.argv[3]
    }
    print('Creando usuario {}'.format(u))

    from users.model import obtener_sesion, UsersModel
    with obtener_session() as s:
        uid = UsersModel.crear_usuario(s, u)
        UsersModel.cambiar_clave(s, uid, sys.argv[4])
        s.commit()