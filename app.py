import falcon
from .resources import Search, Detail

app = application = falcon.App()

search = Search()
detail = Detail()
app.add_route('/search', search)
app.add_route('/detail', detail)
