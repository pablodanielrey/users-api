from .GoogleAuthApi import GoogleAuthApi


class GoogleModel:

    @classmethod
    def sincronizar(cls, uid):
        userGoogle = s.dni + '@econo.unlp.edu.ar'
        service = GAuthApis.getServiceAdmin()
        r = service.users().update(userKey=userGoogle,body=datos).execute()

        r = service.users().aliases().list(userKey=userGoogle).execute()
        aliases = [a['alias'] for a in r.get('aliases', [])]
        for e in s.emails.split(","):
            if e not in aliases:
                logging.debug('creando alias')
                r = service.users().aliases().insert(userKey=userGoogle,body={"alias":e}).execute()

    @classmethod
    def insertar_usuario(cls):
        # crear usuario
        datos = {}
        datos["aliases"] = s.emails.split(",")
        datos["changePasswordAtNextLogin"] = False
        datos["primaryEmail"] = userGoogle
        datos["emails"] = [{'address': userGoogle, 'primary': True, 'type': 'work'}]

        datos["name"] = {"givenName": user["nombre"], "fullName": fullName, "familyName": user["apellido"]}
        datos["password"] = s.clave
        datos["externalIds"] = [{'type': 'custom', 'value': s.id}]

        r = service.users().insert(body=datos).execute()


        # crear alias
        for e in s.emails.split(","):
            print("Correo a agregar enviar como:{}".format(e))
            r = service.users().aliases().insert(userKey=userGoogle,body={"alias":e}).execute()        


    @classmethod
    def agregarAliasEnviarComo(cls, session, name, email, userKeyG):
        alias = {
            'displayName': name,
            'replyToAddress': email,
            'sendAsEmail': email,
            'treatAsAlias': True,
            'isPrimary': False,
            'isDefault': True
        }
        print("enviar como:{}".format(name))
        print("alias:{}".format(alias))
        gmail = GAuthApis.getServiceGmail(userKeyG)

        r = gmail.users().settings().sendAs().list(userId='me').execute()
        aliases = [ a['sendAsEmail'] for a in r['sendAs'] ]
        print('alias encontrados : {} '.format(aliases))


        if alias['sendAsEmail'] not in aliases:
            print('creando alias')
            r = gmail.users().settings().sendAs().create(userId='me', body=alias).execute()
            ds = cls._crearLog(r)
            session.add(ds)
            session.commit()