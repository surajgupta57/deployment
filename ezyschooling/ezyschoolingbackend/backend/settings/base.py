"""
Base settings to build other settings files upon.
"""

import datetime
import os

import dj_database_url
from decouple import config
from django.contrib.messages import constants as messages

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = config("DEBUG", default=True, cast=bool)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "Asia/Kolkata"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True


# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {"default": dj_database_url.config(default=config("DATABASE_URL"))}


# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "backend.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "backend.wsgi.application"


# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.admin",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rangefilter",
    "django_filters",
    "dal",
    "dal_select2",
    "django_tables2",
    "bootstrap4",
    "bootstrap_datepicker_plus",
    "rest_auth",
    "rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.google",
    "fixture_magic",
    # "silk",
    "notifications",
    "django_elasticsearch_dsl",
    "django_elasticsearch_dsl_drf",
    "drf_yasg",
    "corsheaders",
    "ckeditor",
    "ckeditor_uploader",
    "taggit",
    "import_export",
    "django_celery_beat",
    "django_extensions",
    "crispy_forms",
    "nested_admin",
    "django_user_agents",
    "webpush",
    "taggit_selectize",
    "operators",
]

LOCAL_APPS = [
    "accounts.apps.AccountsConfig",
    "admission_informations",
    "analatics",
    "admission_forms.apps.AdmissionFormsConfig",
    "articles.apps.ArticlesConfig",
    "brands.apps.BrandsConfig",
    "categories.apps.CategoriesConfig",
    "childs.apps.ChildsConfig",
    "core.apps.CoreConfig",
    "discussions.apps.DiscussionsConfig",
    "experts.apps.ExpertsConfig",
    "news.apps.NewsConfig",
    "parents.apps.ParentsConfig",
    "miscs.apps.MiscsConfig",
    "quiz.apps.QuizConfig",
    "schools.apps.SchoolsConfig",
    "tags.apps.TagsConfig",
    "videos.apps.VideosConfig",
    "notification",
    "payments",
    "courses.apps.CoursesConfig",
    "newsletters.apps.NewslettersConfig",
    "custom_admin.apps.CustomAdminConfig",
    "phones.apps.PhonesConfig",
    "careers.apps.CareersConfig",
    "ownelasticsearch.apps.OwnelasticsearchConfig",
    "faqs.apps.FaqsConfig",
    "admin_custom.apps.AdminCustomConfig",
]

# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "accounts.User"

REST_AUTH_TOKEN_MODEL = "accounts.models.Token"

REST_AUTH_TOKEN_CREATOR = "accounts.utils.custom_create_token"

# This is how long a token can exist before it expires. The setting should be set to an instance of datetime.timedelta. The default is 10 hours (timedelta(hours=10)).
TOKEN_TTL = datetime.timedelta(days=15)

# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
# LOGIN_REDIRECT_URL = "users:redirect"

# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
# LOGIN_URL = "account_login"


# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
# AUTH_PASSWORD_VALIDATORS = [
#     {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
#     {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
#     {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
#     {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
# ]


# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
]
# MIDDLEWARE.insert(1, "silk.middleware.SilkyMiddleware",)  # noqa F405

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"

# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"


# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]


# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"


# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# EMAIL_BACKEND = config(
#     "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
# )
# # https://docs.djangoproject.com/en/2.2/ref/settings/#email-timeout
# EMAIL_TIMEOUT = 5

DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL", default="noreply@ezyrecruitment.in")
DEFAULT_TO_SCHOOL_EMAIL = config('DEFAULT_TO_SCHOOL_EMAIL')
DEFAULT_TO_PARENT_EMAIL = config('DEFAULT_TO_PARENT_EMAIL')
FIREBASE_WEBPUSH_KEY = config('FIREBASE_WEBPUSH_KEY')
DJANGO_SERVER_EMAIL = DEFAULT_FROM_EMAIL
IS_PERIODIC_TASK_ACTIVATED = config("IS_PERIODIC_TASK_ACTIVATED", default=False, cast=bool)
EMAIL_SUBJECT_PREFIX = config("DJANGO_EMAIL_SUBJECT_PREFIX", default="Ezyschooling")

EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")

FRESHMARKETER_API_KEY = config("FRESHMARKETER_API_KEY")

GOOGLE_MAP_API_KEY = config("GOOGLE_MAP_API_KEY")

FRESHMARKETER_LIST_ID = config("FRESHMARKETER_LIST_ID")
WHATSAPP_HSM_USER_ID = config("WHATSAPP_HSM_USER_ID")
WHATSAPP_HSM_USER_PASSWORD = config("WHATSAPP_HSM_USER_PASSWORD")


# To convert pdf to images for single merged pdf downloading
LOCAL_DOWNLOAD_PATH = config('LOCAL_DOWNLOAD_PATH')
# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
# ADMINS = [("Mayank", "mayank@ezyschooling.com"),]
#ADMINS = [("Mayank", "mayank@ezyschooling.com"),
#          ("Udit Mittal", "mittaludit98@gmail.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
#MANAGERS = [("Mayank", "mayank@ezyschooling.com"),
#            ("Udit Mittal", "mittaludit98@gmail.com")]


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
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


# Your stuff...
# ------------------------------------------------------------------------------

OLD_PASSWORD_FIELD_ENABLED = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # "rest_framework.authentication.BasicAuthentication",
        "accounts.authentication.ExpiringTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend", 'rest_framework.filters.SearchFilter'],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DATE_INPUT_FORMATS": ["iso-8601", "%Y-%m-%dT%H:%M:%S.%fZ"],
}

REST_AUTH_SERIALIZERS = {
    # "PASSWORD_CHANGE_SERIALIZER": "accounts.api.v1.serializers.CustomPasswordChangeSerializer",
    # "PASSWORD_RESET_SERIALIZER": "accounts.api.v1.serializers.CustomPasswordResetSerializer",
}

REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "parents.api.v1.serializers.ParentRegisterSerializer",
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
]
CORS_ORIGIN_REGEX_WHITELIST = [
    "http://localhost:3000",
]

# Celery
# ------------------------------------------------------------------------------
if USE_TZ:
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_url
CELERY_BROKER_URL = config("CELERY_BROKER_URL")
BROKER_URL = CELERY_BROKER_URL
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_backend
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-accept_content
CELERY_ACCEPT_CONTENT = ["json"]
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_serializer
CELERY_TASK_SERIALIZER = "json"
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_serializer
CELERY_RESULT_SERIALIZER = "json"
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-time-limit
# TODO: set to whatever value is adequate in your circumstances
CELERY_TASK_TIME_LIMIT = 5 * 60
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-soft-time-limit
# TODO: set to whatever value is adequate in your circumstances
CELERY_TASK_SOFT_TIME_LIMIT = 2*60
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#beat-scheduler
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"


CACHE_TTL = 60 * 15

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"

CKEDITOR_CONFIGS = {
    "default": {
        "skin": "office2013",
        "toolbar_Basic": [["Source", "-", "Bold", "Italic"]],
        "toolbar_YourCustomToolbarConfig": [
            {"name": "document", "items": [
                "Source", "-", "Save", "NewPage", "Preview", "Print", "-", "Templates"]},
            {"name": "clipboard", "items": [
                "Cut", "Copy", "Paste", "PasteText", "PasteFromWord", "-", "Undo", "Redo"]},
            {"name": "editing", "items": [
                "Find", "Replace", "-", "SelectAll"]},
            {"name": "forms",
                "items": ["Form", "Checkbox", "Radio", "TextField", "Textarea", "Select", "Button", "ImageButton",
                          "HiddenField"]},
            "/",
            {"name": "basicstyles",
                "items": ["Bold", "Italic", "Underline", "Strike", "Subscript", "Superscript", "-", "RemoveFormat"]},
            {"name": "paragraph",
                "items": ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "Blockquote", "CreateDiv", "-",
                          "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock", "-", "BidiLtr", "BidiRtl",
                          "Language"]},
            {"name": "links", "items": ["Link", "Unlink", "Anchor"]},
            {
                "name": "insert",
                "items": [
                    "Image",
                    "Flash",
                    "Table",
                    "HorizontalRule",
                    "Smiley",
                    "SpecialChar",
                    "PageBreak",
                    "Iframe",
                ],
            },
            "/",
            {"name": "styles", "items": [
                "Styles", "Format", "Font", "FontSize"]},
            {"name": "colors", "items": ["TextColor", "BGColor"]},
            {"name": "tools", "items": ["Maximize", "ShowBlocks"]},
            {"name": "about", "items": ["About"]},
            "/",  # put this to force next toolbar on new line
            {
                "name": "yourcustomtools",
                "items": [
                    # put the name of your editor.ui.addButton here
                    "Preview",
                    "Maximize",
                ],
            },
        ],
        "toolbar": "YourCustomToolbarConfig",  # put selected toolbar config here
        # "toolbarGroups": [{ "name": "document", "groups": [ "mode", "document", "doctools" ] }],
        # "height": 291,
        # "width": "100%",
        # "filebrowserWindowHeight": 725,
        # "filebrowserWindowWidth": 940,
        # "toolbarCanCollapse": True,
        # "mathJaxLib": "//cdn.mathjax.org/mathjax/2.2-latest/MathJax.js?config=TeX-AMS_HTML",
        "tabSpaces": 4,
        "extraPlugins": ",".join([
            "uploadimage",  # the upload image feature
            # your extra plugins here
            "div",
            "autolink",
            "autoembed",
            "embedsemantic",
            "autogrow",
            # "devtools",
            "widget",
            "lineutils",
            "clipboard",
            "dialog",
            "dialogui",
            "elementspath"
        ]),
    }
}
CRISPY_TEMPLATE_PACK = "bootstrap4"

IMPORT_EXPORT_USE_TRANSACTIONS = True


MESSAGE_TAGS = {
    messages.ERROR: 'danger',
    messages.SUCCESS: 'success',
}

ACCOUNT_USERNAME_REQUIRED = False

# django-allauth
# ------------------------------------------------------------------------------
# ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = 'none'
# https://django-allauth.readthedocs.io/en/latest/configuration.html # ACCOUNT_EMAIL_REQUIRED = True
# https://django-allauth.readthedocs.io/en/latest/configuration.html
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
# ACCOUNT_ADAPTER = "ezyadmissions.users.adapters.AccountAdapter"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
# SOCIALACCOUNT_ADAPTER = "ezyadmissions.users.adapters.SocialAccountAdapter"

ACCOUNT_UNIQUE_EMAIL = True


# Elasticsearch DSL config
ELASTICSEARCH_DSL = {
    "default": {
        "hosts": config("ELASTICSEARCH_DSL_HOST", default="localhost:9200"),
        "http_auth": [config("ELASTIC_USER", default="elastic"), config("ELASTIC_PASSWORD")],
    },
}
ELASTIC_SEARCH_INDEX = config('ELASTIC_INDEX_NAME',default='prod1-school-profile')

USER_AGENTS_CACHE = "default"


WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "BL86foluWqlf0NLj97txbjWiecgo_8jqKhGMccXA54ANZsAJ5MfMUN9AgFYlgSj5EYk8Gu43Q7bU6wpr7Apjr-k",
    "VAPID_PRIVATE_KEY": "x_c-UtnhjN_pkISehbYr8INcpBNU_sa5U-6_Q0WnVUU",
    "VAPID_ADMIN_EMAIL": "shekharnunia@gmail.com"
}
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760


# TAGGIT_CASE_INSENSITIVE = True

TAGGIT_TAGS_FROM_STRING = "taggit_selectize.utils.parse_tags"
TAGGIT_STRING_FROM_TAGS = "taggit_selectize.utils.join_tags"

TAGGIT_SELECTIZE_THROUGH = "tags.models.CustomTag"


DJANGO_TABLES2_TEMPLATE="django_tables2/bootstrap4.html"

GOOGLE_SHEET_ID = config("GOOGLE_SHEET_ID")
