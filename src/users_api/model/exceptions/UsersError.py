
class UsersError(Exception):
    def __init__(self, status_code=None):
        self.status_code = 500
        if status_code:
            self.status_code=status_code
        self.error = self.__class__.__name__

    def __json__(self):
        return self.__dict__


class FormatoIncorrecto(UsersError):
    def __init__(self):
        super().__init__(status_code=400)

class FormatoDeClaveIncorrectoError(UsersError):
    def __init__(self):
        super().__init__(status_code=400)

class CorreoNoEncontradoError(UsersError):
    def __init__(self):
        super().__init__(status_code=400)
