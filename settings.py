import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.getenv('DB_DIR_PATH'), 'db.sqlite3'),
    }
}

INSTALLED_APPS = (
    'db',
)

SECRET_KEY = os.getenv('DJANGO_SK')
