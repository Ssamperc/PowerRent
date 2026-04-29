import os
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
    'https://*.replit.dev',
    'https://*.repl.co',
    'https://*.replit.app',
    'http://localhost:5000',
    'http://0.0.0.0:5000',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use Replit's PostgreSQL database if DATABASE_URL is available
if os.environ.get('DATABASE_URL'):
    import urllib.parse
    db_url = urllib.parse.urlparse(os.environ['DATABASE_URL'])
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_url.path.lstrip('/').split('?')[0],
            'USER': db_url.username,
            'PASSWORD': db_url.password,
            'HOST': db_url.hostname,
            'PORT': db_url.port or 5432,
        }
    }
