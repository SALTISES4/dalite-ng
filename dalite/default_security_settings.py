# SecurityMiddleware settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_NAME = "__Host-csrftoken"
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 183 * 24 * 60 * 60  # 6-month default
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True

# Sample Django-CSP settings
CSP_BASE_URI = ["'none'"]
CSP_DEFAULT_SRC = ["'self'"]
CSP_FONT_SRC = ["'self'"]
CSP_FORM_ACTION = ["'self'"]
CSP_FRAME_ANCESTORS = ["'none'"]
CSP_FRAME_SRC = ["*"]
CSP_IMG_SRC = ["*", "data:"]
CSP_MEDIA_SRC = ["*", "data:"]
CSP_SCRIPT_SRC = ["'self'"]
CSP_STYLE_SRC = ["'self'"]
CSP_INCLUDE_NONCE_IN = ["script-src", "style-src"]
CSP_UPGRADE_INSECURE_REQUESTS = False
CSP_BLOCK_ALL_MIXED_CONTENT = True
CSP_REPORT_PERCENTAGE = 0.1

# django-permissions-policy
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "camera": [],
    "display-capture": [],
    "document-domain": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "interest-cohort": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "usb": [],
}

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
