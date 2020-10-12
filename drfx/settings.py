import logging.config
import os

# import datetime

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "qv*o1&&x%#jtsn)5((g+yw#%3_a$ykfof6b-)j^i$1a8se*7c8"
ACCOUNT_BIC = "BICCODE"
ACCOUNT_IBAN = "FI12 3456 789"
ACCOUNT_NAME = "Account name"

# The service ID that opens hacklab door. Avoid using in code.
DEFAULT_ACCOUNT_SERVICE = 2

CUSTOM_INVOICE_REFERENCE_BASE = 10000
SERVICE_INVOICE_REFERENCE_BASE = 20000

MEMBERSHIP_APPLICATION_NOTIFY_ADDRESS = "example@example.com"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "*",
]

# Sitename
SITENAME = "Mulysa"
SITE_URL = "https://mulysa.tld"
PRIVACY_POLICY_URL = "https://example.com/privacy_policy.html"

# External urls, like links to members guide and rules
ASSOCIATION_RULES_URL = (
    "https://tampere.hacklab.fi/pages/yhdistyksen-s%C3%A4%C3%A4nn%C3%B6t/"
)
MEMBERS_GUIDE_URL = "https://wiki.tampere.hacklab.fi/member_s_guide"
GITHUB_URL = "https://github.com/TampereHacklab/mulysa"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # nice to have, mainly shell_plus :)
    "django_extensions",
    "log_request_id",
    # drf and its authentication friends
    "rest_framework",
    "rest_framework.authtoken",
    "rest_auth",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # for logging some sensitive endpoints like access
    "rest_framework_tracking",
    # filters
    "django_filters",
    "rest_framework_filters",
    # email queue
    "mailer",
    # ready made registration please
    # todo: we probably want to write our own
    "rest_auth.registration",
    # our api and other apps
    "api",
    "users",
    "www",
    "emails",
    # so that we don't have to write
    # hundreds of lines of css
    "bootstrap4",
]

AUTH_USER_MODEL = "users.CustomUser"

# use the management command update_local_bootstrap to fetch the files
# and to get this section when needed
BOOTSTRAP4 = {
    'css_url': '/static/www/bootstrap4/bootstrap.min.css',
    'javascript_url': '/static/www/bootstrap4/bootstrap.min.js',
    'jquery_slim_url': '/static/www/bootstrap4/jquery-3.5.1.slim.min.js',
    'jquery_url': '/static/www/bootstrap4/jquery-3.5.1.min.js',
    'popper_url': '/static/www/bootstrap4/popper.min.js'
}

MIDDLEWARE = [
    "log_request_id.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "user_language_middleware.UserLanguageMiddleware",
]

ROOT_URLCONF = "drfx.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["www/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "www.context_processors.external_urls",
            ],
        },
    },
]

WSGI_APPLICATION = "drfx.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "fi"

LANGUAGES = [
    ("fi", ("Suomi")),
    ("en", ("English")),
]

LOCALE_PATHS = ("locale",)

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

AUTH_USER_MODEL = "users.CustomUser"

SITE_ID = 1

# NOTE: remember to set these to something sane in your settings_local for production!
# utils.emailbackend has a nice smtp backend with logging available
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
MAILER_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
NOREPLY_FROM_ADDRESS = "noreply@mulysa.host.invalid"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        # by default we don't want to give any permissions to anyone
        "rest_framework.permissions.IsAdminUser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework_filters.backends.RestFrameworkFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
}

# tell all auth to use email as username
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
OLD_PASSWORD_FIELD_ENABLED = True

LOGGING_CONFIG = None
LOGLEVEL = os.environ.get("LOGLEVEL", "info").upper()
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": "log_request_id.filters.RequestIDFilter"}},
        "formatters": {
            "default": {
                "()": "django.utils.log.ServerFormatter",
                "format": "[{asctime}] {request_id} {levelname} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["request_id",],
            },
        },
        "loggers": {
            # default for all undefined Python modules
            "": {"level": "WARNING", "handlers": ["console",],},
            "users": {"level": LOGLEVEL, "handlers": ["console",], "propagate": False,},
            "utils": {"level": LOGLEVEL, "handlers": ["console",], "propagate": False,},
            "django.server": {
                "handlers": ["console",],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
)

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# sms sending
SMS = {
    "ENABLED": os.environ.get("SMS_ENABLED", "False").lower() == "true",
    "TWILIO_SID": os.environ.get("TWILIO_SID", ""),
    "TWILIO_TOKEN": os.environ.get("TWILIO_TOKEN", ""),
    "TWILIO_FROM": os.environ.get("TWILIO_FROM", ""),
    "TO_NUMBER": os.environ.get("SMS_TO", ""),
}


# Import just to get in the translation context
# from utils import businesslogic


# Load non-default settings from settings_local.py if it exists
try:
    from .settings_local import *  # noqa
except ImportError:
    pass
