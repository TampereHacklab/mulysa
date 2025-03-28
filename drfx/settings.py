import logging.config
import os
import sys

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


# After user has been marked for deletion, how many days to wait until
# really deleting the user and their associated data
USER_DELETION_DAYS = 90

# https://docs.djangoproject.com/en/4.1/ref/settings/
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Sitename
SITENAME = "Mulysa"
SITE_URL = "https://mulysa.tld"
PRIVACY_POLICY_URL = "https://example.com/privacy_policy.html"


# these are for the receipt functionality
RECEIPTNAME = "Mulysa ry"
RECEIPTREGID = "1234567-8"
RECEIPTSTREET = "Street 12, Somewhere Finland"

# Matrix integration

# Access token for user you want to use. Leave empty for no Matrix integration.
MATRIX_ACCESS_TOKEN = ""
# Matrix homeserver URL
MATRIX_SERVER = "https://matrix.hacklab.fi"
# Room ID to invite new users. Default points to Hacklab.fi Matrix space.
MATRIX_ROOM_ID = "!yNczWCtqHFeWuTbmhB:hacklab.fi"
# URL to register to Matrix, if no account provided
MATRIX_ACCOUNT_CRETION_URL = "https://chat.hacklab.fi/#/login"
# Site specific help text for registration
MATRIX_ACCOUNT_CRETION_HELP = "Choose Continue with Hacklab Finland Keycloack"

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
    "django.contrib.humanize",
    # nice to have, mainly shell_plus :)
    "django_extensions",
    "log_request_id",
    # drf and its authentication friends
    "rest_framework",
    "rest_framework.authtoken",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    # for logging some sensitive endpoints like access
    "rest_framework_tracking",
    # filters
    "django_filters",
    "rest_framework_filters",
    # email queue
    "mailer",
    # range filter for admin
    "rangefilter",
    # ready made registration please
    # todo: we probably want to write our own
    # constance settings manager
    "constance.backends.database",
    "constance",
    # our api and other apps
    "api",
    "users",
    "www",
    "emails",
    # so that we don't have to write
    # hundreds of lines of css
    "bootstrap4",
    # oauth provider for keycloack integration
    "oauth2_provider",
    # nordigen banking data automation
    "nordigenautomation",
]

AUTH_USER_MODEL = "users.CustomUser"

# more secure cookies
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "__Host-sessionid"
LANGUAGE_COOKIE_HTTPONLY = True
LANGUAGE_COOKIE_SECURE = True
LANGUAGE_COOKIE_SAMESITE = "Strict"
LANGUAGE_COOKIE_NAME = "__Host-language"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_NAME = "__Host-csrf"

# use the management command update_local_bootstrap to fetch the files
# and to get this section when needed
BOOTSTRAP4 = {
    "css_url": "/static/www/bootstrap4/bootstrap.min.css",
    "javascript_url": "/static/www/bootstrap4/bootstrap.bundle.min.js",
    "jquery_slim_url": "/static/www/bootstrap4/jquery-3.5.1.slim.min.js",
    "jquery_url": "/static/www/bootstrap4/jquery-3.5.1.min.js",
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
    "users.middleware.language.UserLanguageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
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


# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
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
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
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
                "filters": [
                    "request_id",
                ],
            },
        },
        "loggers": {
            # default for all undefined Python modules
            "": {
                "level": "WARNING",
                "handlers": [
                    "console",
                ],
            },
            "users": {
                "level": LOGLEVEL,
                "handlers": [
                    "console",
                ],
                "propagate": False,
            },
            "utils": {
                "level": LOGLEVEL,
                "handlers": [
                    "console",
                ],
                "propagate": False,
            },
            "nordigenautomation": {
                "level": DEBUG,
                "handlers": [
                    "console",
                ],
                "propagate": False,
            },
            "django.server": {
                "handlers": [
                    "console",
                ],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
)

if len(sys.argv) > 1 and sys.argv[1] == "test":
    logging.disable(logging.CRITICAL)

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

OAUTH2_PROVIDER = {
    "OAUTH2_VALIDATOR_CLASS": "api.mulysaoauthvalidator.MulysaOAuth2Validator",
    "OIDC_ENABLED": True,
    # keep pre2.0 behaviour see https://django-oauth-toolkit.readthedocs.io/en/latest/changelog.html#id7
    "PKCE_REQUIRED": False,
    "SCOPES": {
        "openid": "OpenID Connect scope",
    },
}

# Import just to get in the translation context
# from utils import businesslogic

# Load non-default settings from settings_local.py if it exists
try:
    from .settings_local import *  # noqa
except ImportError:
    pass

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

# Constance config - settings for the app that are editable in django admin
# Edit as desired to change what can be configured in the GUI
# See https://django-constance.readthedocs.io/en/latest/index.html#configuration

CONSTANCE_CONFIG = {
    "ASSOCIATION_RULES_URL": (
        ASSOCIATION_RULES_URL,
        "Link to the rules of the association",
        str,
    ),
    "MEMBERS_GUIDE_URL": (
        MEMBERS_GUIDE_URL,
        "Link to the guide for new members",
        str,
    ),
    "PRIVACY_POLICY_URL": (
        PRIVACY_POLICY_URL,
        "Link to privacy policy",
        str,
    ),
    # Receipt functionality configuration
    "RECEIPT_NAME": (RECEIPTNAME, "Name of the association to show on receipts", str),
    "RECEIPT_REGID": (RECEIPTREGID, "ID of the association to show on receipts", str),
    "RECEIPT_ADDRESS": (
        RECEIPTSTREET,
        "Address to show on receipts",
        str,
    ),
    "GITHUB_URL": (GITHUB_URL, "Link to the github repository", str),
    "MATRIX_SERVER": (MATRIX_SERVER, "Matrix server", str),
    "MATRIX_MEMBER_ROOM_ID": (MATRIX_ROOM_ID, "Matrix room id for members", str),
    "HIDE_CUSTOM_INVOICE": (
        False,
        "Hide the custom invoice feature for end users",
        bool,
    ),
    # Uncomment this if you would like to be able to edit the bank account details in the admin panel
    # "ACCOUNT_IBAN": (ACCOUNT_IBAN, "IBAN of the association's bank account"),
    # "ACCOUNT_BIC": (ACCOUNT_BIC, "BIC of the association's bank account"),
    # "ACCOUNT_NAME": (ACCOUNT_NAME, "Name of the association's bank account"),
}
