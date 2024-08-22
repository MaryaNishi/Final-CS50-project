from flask_caching import Cache

cache = Cache()

def init_app(app):
    app.config['CACHE_TYPE'] = 'simple' 
    cache.init_app(app)

DEBUG = True



