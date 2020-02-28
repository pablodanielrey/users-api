
class ResetClaveError(Exception):

    def __init__(self, status_code=None):
        self.status_code = 500
        if status_code:
            self.status_code=status_code
        self.error = self.__class__.__name__

    def __json__(self):
        return self.__dict__

class TokenExpiradoError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=403)

class SeguridadError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=403)

class UsuarioNoEncontradoError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=404)

class NoTieneCuentaAlternativaError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=404)

class CodigoIncorrectoError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=400)

class EnvioCodigoError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=500)

class LimiteDeEnvioError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=400)

class LimiteDeVerificacionError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=403)

class ClaveError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=500)

class CorreoBloqueadoError(ResetClaveError):
    def __init__(self):
        super().__init__(status_code=500)
