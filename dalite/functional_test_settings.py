from .settings import *  # noqa

MANAGERS = [
    ("test_manager_1", "test_manager_1@mydalite.org"),
    ("test_manager_2", "test_manager_2@mydalite.org"),
    ("test_manager_3", "test_manager_3@mydalite.org"),
]
DEFAULT_PASSWORD = "default_password"

DEBUG = False

DEFAULT_SCHEME_HOST_PORT = "http://nginx:8080"

SSL_CONTEXT = False
SECURE_HSTS_SECONDS = 0
CSRF_COOKIE_NAME = "csrftoken"

CSRF_COOKIE_SECURE = SSL_CONTEXT
SECURE_SSL_REDIRECT = SSL_CONTEXT
SESSION_COOKIE_SECURE = SSL_CONTEXT
CSP_UPGRADE_INSECURE_REQUESTS = SSL_CONTEXT
LANGUAGE_COOKIE_SECURE = SSL_CONTEXT
