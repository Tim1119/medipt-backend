from pathlib import Path
import os
import cloudinary 
import environ
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))

#---------------------------------------------------------- READING ENV FILES ---------------------------------------------------------
environ.Env.read_env(BASE_DIR / ".env")



#----------------------------------------------  PROJECT SETTINGS ---------------------------------------------------------------
SECRET_KEY=env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(" ")




# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.organizations',
    'apps.caregivers',
    'apps.patients',
    'apps.invites',
]

THIRD_PARTY_APPS=[
    'cloudinary_storage',  # Add before imagekit if still using it
    'cloudinary',
    'imagekit',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_standardized_errors',
    'django_celery_results',
    'drf_yasg',
    'corsheaders',

]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS 

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'medipt.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'medipt.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_NAME'),         
        'USER': env('DATABASE_USER'),         
        'PASSWORD': env('DATABASE_PASSWORD'), 
        'HOST': env('DATABASE_HOST'),           
        'PORT': env('DATABASE_PORT'),            
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Lagos'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
# STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# STATICFILES_DIRS = [BASE_DIR / "static",]


MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'





AUTH_USER_MODEL = 'accounts.User'

DRF_STANDARDIZED_ERRORS = {"EXCEPTION_FORMATTER_CLASS": "shared.custom_exception_handler.MyExceptionFormatter"}

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    'DEFAULT_RENDERER_CLASSES': (
        'shared.custom_renderer.SuccessJsonRenderer',
       'rest_framework.renderers.BrowsableAPIRenderer',
       'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
         'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5000),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'BLACKLIST_ENABLED': True,
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
}


SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,  # Prevents login redirection
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
}


CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = True

INVITATION_EXPIRY_DAYS = 7  # Default to 7 days
MAX_INVITATION_RESENDS = 3  # Maximum resends allowed

cloudinary.config(
    cloud_name=env('CLOUDINARY_CLOUD_NAME'),
    api_key=env('CLOUDINARY_API_KEY'),
    api_secret=env('CLOUDINARY_API_SECRET'),
    secure=True
)