from .settings import *  # noqa

AXES_ENABLED = False

DEBUG = False
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

WATCH = True

SSL_CONTEXT = False
SECURE_HSTS_SECONDS = 0
CSRF_COOKIE_NAME = "csrftoken"

CSRF_COOKIE_SECURE = SSL_CONTEXT
SECURE_SSL_REDIRECT = SSL_CONTEXT
SESSION_COOKIE_SECURE = SSL_CONTEXT
CSP_UPGRADE_INSECURE_REQUESTS = SSL_CONTEXT
LANGUAGE_COOKIE_SECURE = SSL_CONTEXT

# Celery
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "max_retries": 0,
}

# LTI
LTI_STANDALONE_CLIENT_KEY = "standalone_key"
LTI_STANDALONE_CLIENT_SECRET = "standalone_secret"
LTI_BASIC_CLIENT_KEY = "basic_key"
LTI_BASIC_CLIENT_SECRET = "basic_secret"
PYLTI_CONFIG = {
    "consumers": {
        LTI_STANDALONE_CLIENT_KEY: {"secret": LTI_STANDALONE_CLIENT_SECRET},
        LTI_BASIC_CLIENT_KEY: {"secret": LTI_BASIC_CLIENT_SECRET},
    }
}

ROOT_URLCONF = "dalite.test_urls"
