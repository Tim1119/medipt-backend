from .base import *
import logging.config
import logging
from django.utils.log import DEFAULT_LOGGING



CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_RESULT_EXPIRES = 3600  # Task state expires after 1 hour
CELERY_TIMEZONE = 'Africa/Lagos'

REACT_FRONTEND_URL = 'http://localhost:5173'

EMAIL_USE_TLS=True
EMAIL_HOST=env('DEVELOPMENT_EMAIL_HOST')
EMAIL_HOST_USER=env('DEVELOPMENT_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=env('DEVELOPMENT_EMAIL_HOST_PASSWORD')
EMAIL_PORT=env('DEVELOPMENT_EMAIL_PORT')

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  
    "http://localhost:5174",  
    "http://localhost:5173",  
]

CORS_ALLOW_CREDENTIALS = True


# CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Allow JS to read CSRF token


# SESSION_COOKIE_DOMAIN = "localhost"
# CSRF_COOKIE_DOMAIN = "localhost"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_SAMESITE = 'Lax'  # default

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = BASE_DIR / "media"





# -------------------------------------------------------- LOGS --------------------------------------------------
logger = logging.getLogger(__name__)

LOG_LEVEL = "INFO"

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
            },
            "file": {"format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"},
            "django.server": DEFAULT_LOGGING["formatters"]["django.server"],
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
            },
            "file": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "formatter": "file",
                "filename": "logs/medipt.log",
            },
            "django.server": DEFAULT_LOGGING["handlers"]["django.server"],
        },
        "loggers": {
            "": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
            "apps": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "django.server": DEFAULT_LOGGING["loggers"]["django.server"],
        },
    }
)
