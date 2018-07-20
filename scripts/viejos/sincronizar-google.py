"""
    codigo que estaba dentor del modulo de usuarios que hace falta mover a un proyecto aparte
"""

def sincronizar_usuario(uid):
    t = Sincronizador(uid)
    t.start()

def sincronizar_usuario_interno(uid):
    url = '{}{}{}'.format(GOOGLE_API_URL, '/google_usuario/', uid)
    logging.info('sincronizar google - {}'.format(url))
    r = requests.get(url)
    if r.status_code != 200:
        logging.info(r)
    logging.info(r.content)
    logging.info('fin sincronizar google')

class Sincronizador(threading.Thread):
   def __init__(self, uid):
      threading.Thread.__init__(self)
      self.uid = uid

   def run(self):
       sincronizar_usuario_interno(self.uid)
