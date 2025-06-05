from .base import *
import dj_database_url
# Production-specific settings
DEBUG=True


# Production database settings
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': env('DATABASE_NAME'),
#         'USER': env('DATABASE_USER'),
#         'PASSWORD': env('DATABASE_PASSWORD'),
#         'HOST': env('DATABASE_HOST'),
#         'PORT': env('DATABASE_PORT'),
#         'OPTIONS': {
#             'sslmode': env('DATABASE_SSL_MODE', default='require')  # important for Neon
#         },
#     }
# }


DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}





# Production CORS settings
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS').split(' ')

# Production email settings
EMAIL_USE_TLS=True
EMAIL_HOST=env('DEVELOPMENT_EMAIL_HOST')
EMAIL_HOST_USER=env('DEVELOPMENT_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=env('DEVELOPMENT_EMAIL_HOST_PASSWORD')
EMAIL_PORT=env('DEVELOPMENT_EMAIL_PORT')

# Production security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Production logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/medipt.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


# CELERY_BROKER_URL = "redis://localhost:6379/0"
# CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

CELERY_BROKER_URL=redis://default:FszoolJkRjqAFZXieycVFIEazGFgPCKF@ballast.proxy.rlwy.net:27731
CELERY_RESULT_BACKEND=redis://default:FszoolJkRjqAFZXieycVFIEazGFgPCKF@ballast.proxy.rlwy.net:27731
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_EXPIRES = 3600  # Task state expires after 1 hour
CELERY_TIMEZONE = 'Africa/Lagos'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

CORS_ALLOWED_ORIGINS = [
    # "https://medipt-frontend.vercel.app",
    # "https://medipt-frontend-1nubiayaw-timthegreat.vercel.app",
    "*"
]

CSRF_TRUSTED_ORIGINS = [
    # "https://medipt-frontend.vercel.app",
    "*"
]

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage' 

