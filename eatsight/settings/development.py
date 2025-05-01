from .base import *

# Debug is always True in development
DEBUG = True

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'eatsight'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# CORS in development allows all
CORS_ALLOW_ALL_ORIGINS = True

# Email settings for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'