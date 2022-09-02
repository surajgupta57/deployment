from decouple import config
from django.core.mail import get_connection

from .base import *  # noqa

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = config("DJANGO_SECRET_KEY", default="!!!SET DJANGO_SECRET_KEY!!!",)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "192.168.116.215", "192.168.29.153", "192.168.29.176"]


# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa F405


# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = "localhost"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025
EMAIL_HOST_USER = "me@gmail.com"
EMAIL_HOST_PASSWORD = "password"

EMAIL_CONNECTION = get_connection(
            host=config('AWS_EMAIL_HOST'),
            port=config('AWS_EMAIL_PORT'),
            username=config('AWS_EMAIL_USERNAME'),
            password=config('AWS_EMAIL_PASSWORD'),
            use_tls=True
)


# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += [
    "debug_toolbar",
    # 'silk',
]  # noqa F405

# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]  # noqa F405

# MIDDLEWARE.insert(1, 'silk.middleware.SilkyMiddleware',)  # noqa F405

# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]

# Celery
# ------------------------------------------------------------------------------
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = True
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = True

# Your stuff...
# ------------------------------------------------------------------------------

SILKY_PYTHON_PROFILER = True
