import datetime
import os
import warnings

try:
    from .default_security_settings import *  # noqa F403
except ImportError:
    warnings.warn(
        """
        File default_security_settings.py not found.
        You probably want to add it.
        """
    )

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

if os.environ.get("ALLOWED_HOST"):
    ALLOWED_HOSTS.append(os.environ.get("ALLOWED_HOST"))

# Set default url for things like signin links when no request is available
DEFAULT_SCHEME_HOST_PORT = "http://localhost:8000"

# Application definition
INSTALLED_APPS = (
    "daphne",
    "user_feedback",
    "course_flow.apps.CourseFlowConfig",
    "rest_framework",
    "analytics",
    "reputation",
    "quality",
    "tos",
    "peerinst",
    "blink",
    "saltise",
    "channels",
    "REST",
    "teacher",
    "django_elasticsearch_dsl",
    "lti_provider",
    "tinymce",
    "csp",
    "cookie_consent",
    "components",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "compressor",
    "analytical",
    "axes",
    "django_minify_html",
    "django_inlinecss",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "peerinst.middleware.LTIAccessMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "dalite.custom_middleware.resp_405_middleware",
    "dalite.custom_middleware.resp_503_middleware",
    "dalite.cookie_consent.CleanCookiesFixMiddleware",
    "django_minify_html.middleware.MinifyHtmlMiddleware",
    "axes.middleware.AxesMiddleware",
    "ratelimit.middleware.RatelimitMiddleware",
)

ROOT_URLCONF = "dalite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "course_flow.context_processors.update_notifications",
            ]
        },
    }
]

WSGI_APPLICATION = "dalite.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DALITE_DB_NAME", "dalite_ng"),
        "USER": os.environ.get("DALITE_DB_USER", "dalite"),
        "PASSWORD": os.environ.get("DALITE_DB_PASSWORD", ""),
        "HOST": os.environ.get("DALITE_DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DALITE_DB_PORT", "3306"),
        "OPTIONS": {"init_command": "set sql_mode='STRICT_TRANS_TABLES'"},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Caching
MEMCACHE_ADDRESS = os.environ.get("MEMCACHE_ADDRESS", "127.0.0.1")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": f"{MEMCACHE_ADDRESS}:11211",
    }
}

# Custom authentication for object-level permissions
AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesBackend",
    "peerinst.backends.CustomPermissionsBackend",
    "peerinst.lti.LTIBackendStudentsOnly",
)

# Password validators through django-password-validation (backport from 1.9)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"  # noqa
    },
]

# Internationalization
LANGUAGE_CODE = "en"
LANGUAGES = (("fr", "FR"), ("en", "EN"))

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)


# Compressor
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT


# Email
# - Ensure default is console backend
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "emails")


# Login
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "welcome"


# DRF
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ]
}


# Channels
ASGI_APPLICATION = "dalite.routing.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (
                    os.environ.get("CHANNELS_REDIS_ADDRESS", "127.0.0.1"),
                    os.environ.get("CHANNELS_REDIS_PORT", 6379),
                )
            ],
        },
    },
}


# Axes
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = datetime.timedelta(minutes=5)
AXES_LOCKOUT_TEMPLATE = "registration/lockout.html"

# LTI integration
# these are sensitive settings, so it is better to fail early than use some
# defaults visible on public repo
LTI_BASIC_CLIENT_KEY = os.environ.get("LTI_BASIC_CLIENT_KEY", "")
LTI_BASIC_CLIENT_SECRET = os.environ.get("LTI_BASIC_CLIENT_SECRET", "")
LTI_STANDALONE_CLIENT_KEY = os.environ.get("LTI_STANDALONE_CLIENT_KEY", "")
LTI_STANDALONE_CLIENT_SECRET = os.environ.get(
    "LTI_STANDALONE_CLIENT_SECRET", ""
)
LTI_PROPERTY_LIST_EX = [
    "context_title",
    "custom_teacher_id",
    "custom_assignment_id",
    "custom_question_id",
]
LTI_TOOL_CONFIGURATION = {
    "title": "myDALITE",
    "description": "Asynchronous peer instruction",
    "launch_url": "lti/",
    "embed_url": "",
    "embed_icon_url": "",
    "embed_tool_id": "",
    "landing_url": "/student/lti/",
    "course_aware": False,
    "course_navigation": False,
    "new_tab": False,
    "frame_width": 600,
    "frame_height": 400,
    "custom_fields": {},
    "allow_ta_access": False,
    "assignments": {},
}
PYLTI_CONFIG = {
    "consumers": {
        LTI_STANDALONE_CLIENT_KEY: {"secret": LTI_STANDALONE_CLIENT_SECRET},
        LTI_BASIC_CLIENT_KEY: {"secret": LTI_BASIC_CLIENT_SECRET},
    }
}


# CourseFlow settings
COURSE_FLOW_RETURN_URL = {"name": "welcome", "title": "myDalite"}
RATELIMIT_VIEW = "course_flow.views.ratelimited_view"

# Cookie consent
COOKIE_CONSENT_NAME = "cookie_consent"
COOKIE_CONSENT_LOG_ENABLED = True

# NB: Object level permissions are checked for certain models, including
# Question
# TEACHER_GROUP will be automatically added to teachers at login This group and
# its permissions need to be set through admin site
TEACHER_GROUP = "Teacher"

DEFAULT_TIMEZONE = "America/Montreal"

# Celery
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "max_retries": 3,
    "interval_start": 0,
    "interval_step": 0.4,
    "interval_max": 2,
}
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_ACKS_LATE = True
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL", "redis://localhost:6379/0"
)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
)

# Tinymce config
try:
    from .tinymce_settings import *  # noqa F403
except ImportError:
    warnings.warn(
        """
        File tinymce_settings.py not found.
        You probably want to add it.
        """
    )

# CSP
CSP_DEFAULT_SRC = [
    "'self'",
    "*.mydalite.org",
    "*.courseflow.ca",
    "ws:",
    "wss:",
]
CSP_SCRIPT_SRC = [
    "'self'",
    "*.mydalite.org",
    "*.courseflow.ca",
    "d3js.org",
    "ajax.googleapis.com",
    "cdn.polyfill.io",
    "www.youtube.com",
    "s.ytimg.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdn.datatables.net",
    "code.jquery.com",
    "cdn.quilljs.com",
]
CSP_STYLE_SRC = [
    "'self'",
    "*.mydalite.org",
    "*.courseflow.ca",
    "fonts.googleapis.com",
    "ajax.googleapis.com",
    "unpkg.com",
    "cdn.jsdelivr.net",
    "code.jquery.com",
    "cdn.datatables.net",
    "cdn.quilljs.com",
]
CSP_FONT_SRC = [
    "'self'",
    "*.mydalite.org",
    "*.courseflow.ca",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "unpkg.com",
]
CSP_OBJECT_SRC = [
    "*.mydalite.org",
    "*.courseflow.ca",
    "phet.colorado.edu",
    "*.youtube.com",
    "*.youtube-nocookie.com",
    "*.vimeo.com",
    "docs.google.com",
    "openstax.org",
    "www.geogebra.org",
]
CSP_FRAME_SRC = CSP_OBJECT_SRC
CSP_FRAME_ANCESTORS = [
    "'self'",
    "moodle.dawsoncollege.qc.ca",
]

ELASTICSEARCH_DSL = {
    "default": {"hosts": "localhost:9200"},
}
ELASTICSEARCH_DSL_AUTOSYNC = False

# Functional tests that scrape web console logs currently require chromedriver
TESTING_BROWSER = "chrome"

try:
    from .local_settings import *  # noqa F403

    try:
        INSTALLED_APPS += LOCAL_APPS  # noqa F405
    except NameError:
        pass
except ImportError:
    warnings.warn(
        "File local_settings.py not found. You probably want to add it -- "
        "see README.md."
    )
    pass


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s | %(asctime)s | %(message)s"},
        "complete": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s: %(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "file_debug_log": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "log/debug.log"),
        },
        "file_student_log": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "log/student.log"),
        },
        "file_teacher_log": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "log/teacher_activity.log"),
        },
        "tos_file_log": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "complete",
            "filename": os.path.join(BASE_DIR, "log/tos.log"),
        },
        "tos_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "peerinst_file_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.FileHandler",
            "formatter": "complete",
            "filename": os.path.join(BASE_DIR, "log", "peerinst.log"),
        },
        "peerinst_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "dalite_file_log": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "log/dalite.log"),
        },
        "dalite_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "quality_file_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.FileHandler",
            "formatter": "complete",
            "filename": os.path.join(BASE_DIR, "log", "quality.log"),
        },
        "quality_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "reputation_file_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.FileHandler",
            "formatter": "complete",
            "filename": os.path.join(BASE_DIR, "log", "reputation.log"),
        },
        "reputation_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "analytics_file_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.FileHandler",
            "formatter": "complete",
            "filename": os.path.join(BASE_DIR, "log", "analytics.log"),
        },
        "analytics_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "search_file_log": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "complete",
            "filename": os.path.join(BASE_DIR, "log", "search.log"),
        },
        "performance_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
        "validation_console_log": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "complete",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["file_debug_log"],
            "level": "DEBUG",
            "propagate": True,
        },
        "peerinst.views": {
            "handlers": ["file_student_log"],
            "level": "INFO",
            "propagate": True,
        },
        "tos-views": {
            "handlers": ["tos_file_log", "tos_console_log"],
            "level": "INFO",
            "propagate": True,
        },
        "tos-models": {
            "handlers": ["tos_file_log", "tos_console_log"],
            "level": "INFO",
            "propagate": True,
        },
        "teacher_activity": {
            "handlers": ["file_teacher_log"],
            "level": "INFO",
            "propagate": True,
        },
        "peerinst-models": {
            "handlers": ["peerinst_file_log", "peerinst_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "peerinst-views": {
            "handlers": ["peerinst_file_log", "peerinst_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "peerinst-auth": {
            "handlers": ["peerinst_file_log", "peerinst_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "peerinst-scheduled": {
            "handlers": ["peerinst_file_log", "peerinst_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "dalite": {
            "handlers": ["dalite_file_log", "dalite_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "quality": {
            "handlers": ["quality_file_log", "quality_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "reputation": {
            "handlers": ["reputation_file_log", "reputation_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "analytics": {
            "handlers": ["analytics_file_log", "analytics_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "performance": {
            "handlers": ["performance_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "REST": {
            "handlers": ["console_log"],
            "level": "DEBUG",
            "propagate": True,
        },
        "validation": {
            "handlers": ["validation_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "nlp": {
            "handlers": ["performance_console_log"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "search": {
            "handlers": ["search_file_log"],
            "level": "INFO",
            "propagate": True,
        },
        "peerinst.tasks": {
            "handlers": ["peerinst_console_log"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
