
import ptvsd
ptvsd.enable_attach(address = ('0.0.0.0', 10104))

from users_api.api.rest.wsgi import app
app.run(host='0.0.0.0', port=10102, debug=False)

