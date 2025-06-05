from .base import *
import dj_database_url
import os

# Production-specific settings
DEBUG = True

# Production database settings
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# CORS Settings - Choose ONE approach:

# Option 1: Allow specific origins (RECOMMENDED for production)
CORS_ALLOWED_ORIGINS = [
    "https://medipt-frontend.vercel.app",
    "https://medipt-frontend-h4h1xvlie-timthegreat.vercel.app",
    "https://medipt-frontend-1nubiayaw-timthegreat.vercel.app",
    # Add any other frontend URLs you're using
]

CSRF_TRUSTED_ORIGINS = [
    "https://medipt-frontend.vercel.app",
    "https://medipt-frontend-h4h1xvlie-timthegreat.vercel.app",
    "https://medipt-frontend-1nubiayaw-timthegreat.vercel.app",
]

# Option 2: Allow all origins (ONLY for development/testing)
# Uncomment these lines and comment out the specific origins above if needed
# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_CREDENTIALS = True

# Additional CORS headers that might be needed
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Production email settings
EMAIL_USE_TLS = True
EMAIL_HOST = env('DEVELOPMENT_EMAIL_HOST')
EMAIL_HOST_USER = env('DEVELOPMENT_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('DEVELOPMENT_EMAIL_HOST_PASSWORD')
EMAIL_PORT = env('DEVELOPMENT_EMAIL_PORT')

# Production security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Celery settings
CELERY_BROKER_URL = "redis://default:FszoolJkRjqAFZXieycVFIEazGFgPCKF@ballast.proxy.rlwy.net:27731"
CELERY_RESULT_BACKEND = "redis://default:FszoolJkRjqAFZXieycVFIEazGFgPCKF@ballast.proxy.rlwy.net:27731"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_EXPIRES = 3600  # Task state expires after 1 hour
CELERY_TIMEZONE = 'Africa/Lagos'

# Logging configuration
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

# Cloudinary storage
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'