from .settings import *  # noqa

AXES_ENABLED = False

DEBUG = False

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
    "landing_url": "lti/student_lti/",
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
    "consumers": {"__consumer_key__": {"secret": "__lti_secret__"}}
}
