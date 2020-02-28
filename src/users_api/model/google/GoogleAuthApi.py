'''
    https://developers.google.com/admin-sdk/directory/
    https://developers.google.com/admin-sdk/directory/v1/reference/users/

    aca estan los scopes
    https://developers.google.com/identity/protocols/googlescopes
'''

import os

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials
import httplib2

class GAuthApis:

    SCOPES = 'https://www.googleapis.com/auth/admin.directory.user'

    SCOPESGMAIL = [
        'https://mail.google.com/',
        'https://www.googleapis.com/auth/gmail.settings.sharing'
    ]

    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']
    """

    @classmethod
    def getCredentials(cls, username, SCOPES=SCOPES):
        ''' genera las credenciales delegadas al usuario username '''
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,'credentials.json')

        credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, SCOPES)

        ''' uso una cuenta de admin del dominio para acceder a todas las apis '''
        admin_credentials = credentials.create_delegated(username)

        return admin_credentials

    @classmethod
    def getService(cls, version, api, scopes, username):
        credentials = cls.getCredentials(username, scopes)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build(api, version, http=http, cache_discovery=False)
        return service

    @classmethod
    def getServiceAdmin(cls, username, version='directory_v1'):
        api='admin'
        return cls.getService(version, api, cls.SCOPES, username)

    @classmethod
    def getServiceGmail(cls, username, version='v1'):
        api='gmail'
        return cls.getService(version, api, cls.SCOPESGMAIL, username)

