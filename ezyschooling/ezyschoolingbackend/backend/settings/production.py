import logging

import dj_database_url
from decouple import config, Csv

# MEDIA
# ------------------------------------------------------------------------------
# region http://stackoverflow.com/questions/10390244/
# Full-fledge class: https://stackoverflow.com/a/18046120/104731
from django.core.mail import get_connection

SECRET_KEY = config("DJANGO_SECRET_KEY")
# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
from .base import *  # noqa

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', default="api.ezyschooling.com", cast=Csv())

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
DATABASES["default"]["CONN_MAX_AGE"] = config("CONN_MAX_AGE", default=60)  # noqa F405

# # CACHES
# # ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }
}


# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'


# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
# SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=True, cast=bool)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
# SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
# CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this tso 60 seconds first and then to 518400 once you prove the former works
# SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
# SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
#     "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool
# )
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
# SECURE_HSTS_PRELOAD = config("DJANGO_SECURE_HSTS_PRELOAD", default=True, cast=bool)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
# SECURE_CONTENT_TYPE_NOSNIFF = config(
#     "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True, cast=bool
# )

# STORAGES
# ------------------------------------------------------------------------------
# https://django-storages.readthedocs.io/en/latest/#installation
INSTALLED_APPS += ["storages",]  # noqa F405
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_ACCESS_KEY_ID = config("DJANGO_AWS_ACCESS_KEY_ID")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_SECRET_ACCESS_KEY = config("DJANGO_AWS_SECRET_ACCESS_KEY")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_STORAGE_BUCKET_NAME = config("DJANGO_AWS_STORAGE_BUCKET_NAME")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_QUERYSTRING_AUTH = False
# DO NOT change these unless you know what you're doing.
_AWS_EXPIRY = 60 * 60 * 24 * 7
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate"
}
#  https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_DEFAULT_ACL = None
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
# AWS_S3_REGION_NAME = config("DJANGO_AWS_S3_REGION_NAME", default=None)


# STATIC
# ------------------------

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


from storages.backends.s3boto3 import S3Boto3Storage  # noqa E402


class StaticRootS3Boto3Storage(S3Boto3Storage):
    location = "static"
    default_acl = "public-read"


class MediaRootS3Boto3Storage(S3Boto3Storage):
    # location = "media"
    file_overwrite = False


# endregion
DEFAULT_FILE_STORAGE = "backend.settings.production.MediaRootS3Boto3Storage"
MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"


# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email

DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL', default="query@ezyschooling.com")

DJANGO_SERVER_EMAIL = DEFAULT_FROM_EMAIL

SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_SUBJECT_PREFIX = '[EzySchooling.com] '

DJANGO_EMAIL_SUBJECT_PREFIX = config('DJANGO_EMAIL_SUBJECT_PREFIX')

EMAIL_BACKEND = config(
    'EMAIL_BACKEND', default="django.core.mail.backends.smtp.EmailBackend")

# Send Pulse Backend
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_CONNECTION = get_connection(
            host=config('AWS_EMAIL_HOST'),
            port=config('AWS_EMAIL_PORT'),
            username=config('AWS_EMAIL_USERNAME'),
            password=config('AWS_EMAIL_PASSWORD'),
            use_tls=True
)

# For AWS
# EMAIL_HOST_AWS = config('EMAIL_HOST_AWS')
# EMAIL_PORT_AWS = config('EMAIL_PORT_AWS', cast=int)
# EMAIL_USE_TLS_AWS = config('EMAIL_USE_TLS_AWS', cast=bool)
# EMAIL_HOST_USER_AWS = config('EMAIL_HOST_USER_AWS')
# EMAIL_HOST_PASSWORD_AWS = config('EMAIL_HOST_PASSWORD_AWS')
# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = config("DJANGO_ADMIN_URL")


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s",
            "style": "{"
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            'filters': ['require_debug_false'],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        # 'mail_admins': {
        #     'level': 'INFO',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'filters': ['require_debug_true']
        # },
        # 'file': {
        #     'level': 'INFO',
        #     'class': 'logging.FileHandler',
        #     'filters' : ['require_debug_false'],
        #     'filename': os.path.join(BASE_DIR,"info.log"),
        # },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
        # 'gunicorn': {
        #     'level': 'DEBUG',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'formatter': 'simple',
        #     # 'filename': '/opt/djangoprojects/reports/bin/gunicorn.errors',
        #     'filename': os.path.join(BASE_DIR,"info.log"),
        #     'maxBytes': 1024 * 1024 * 100,  # 100 mb
        # }
    },
    # "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        #'django': {
        #     'handlers': ['gunicorn'],
        #     'propagate': True,
        #},
        # 'django.request': {
        #     'handlers': ['mail_admins'],
        #     'level': 'ERROR',
        #     'propagate': False,
        # },
        # 'myproject.custom': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': 'INFO',
        #     'filters': ['require_debug_true']
        # },
        # "django.db.backends": {
        #     "level": "ERROR",
        #     "handlers": ["console"],
        #     "propagate": False,
        # },
        # 'gunicorn.errors': {
        #     'level': 'INFO',
        #     'handlers': ['gunicorn'],
        #     'propagate': True,
        # },
        # Errors logged by the SDK itself
        # "sentry_sdk": {"level": "ERROR", "handlers": ["console"], "propagate": False},
        # "django.security.DisallowedHost": {
        #     "level": "ERROR",
        #     "handlers": ["console"],
        #     "propagate": False,
        # },
    },
}

# Your stuff...
# ------------------------------------------------------------------------------
# Razorpay settings
RAZORPAY_ID = config('RAZORPAY_ID')
RAZORPAY_KEY = config('RAZORPAY_KEY')

OTP_VALIDITY_TIME = config("OTP_VALIDITY_TIME", default=300, cast=int)
SMS_API_KEY = config("SMS_API_KEY")
