"""
Django settings for ggquant project.

Generated by 'django-admin startproject' using Django 4.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
from ggquant import my_settings

import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key
with open('.etc/secret_key.txt') as f:
    SECRET_KEY = f.read().strip()


# SECURITY WARNING: don't run with debug turned on in production!
from ggquant.local_settings import LOCAL_DEBUG
DEBUG = LOCAL_DEBUG
ALLOWED_HOSTS = ['43.200.134.113', '.ap-northeast-2.compute.amazonaws.com', 'localhost']

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# Application definition
INSTALLED_APPS = [
    #
    'channels',

    #
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # ggdb
    'ggdb',

    #
    'layout',

    # user
    'user',

    # dashboard
    'dashboard',
    'dashboard.viewmanagers',

    # wiki
    'wiki',
    #
    'django_extensions',
    'sass_processor',
]


# scss
SASS_ROOT = 'static/'
SASS_PROCESSOR_ENABLED = True
SASS_PROCESSOR_ROOT = 'static/'
SASS_OUTPUT_STYLE = 'compact'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'ggquant.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'layout' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'layout.context_processors.categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'ggquant.wsgi.application'

# Channels
from ggquant.local_settings import LOCAL_REDIS_CHANNELS_URL
ASGI_APPLICATION = 'ggquant.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [LOCAL_REDIS_CHANNELS_URL],
        }
    }
}

# Celery
with open('.etc/ggquant_redis_celery_endpoint.txt') as f:
    REDIS_CELERY_URL = f"redis://{f.read().strip()}"
CELERY_BROKER_URL = REDIS_CELERY_URL
CELERY_RESULT_BACKEND = REDIS_CELERY_URL
CELERY_TIMEZONE = 'Asia/Seoul'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = db_settings.DATABASES


# User substitution

AUTH_USER_MODEL = 'user.User'

# AUTHENTICATION_BACKENDS = ['membership.backends.EmailBackend']

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = False


# Statics
STATIC_URL = 'static/'
STATIC_ROOT = '/var/www/ggquant/static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
