import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in {'1', 'true', 'yes', 'on'}


DEBUG = env_bool('DJANGO_DEBUG', True)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-development-only-change-me'
    else:
        raise RuntimeError('DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'blog',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DB_ENGINE = os.environ.get('DJANGO_DB_ENGINE', 'sqlite').lower()
if DB_ENGINE in {'postgres', 'postgresql'}:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['DJANGO_DB_NAME'],
            'USER': os.environ['DJANGO_DB_USER'],
            'PASSWORD': os.environ['DJANGO_DB_PASSWORD'],
            'HOST': os.environ.get('DJANGO_DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DJANGO_DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('DJANGO_DB_CONN_MAX_AGE', '60')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': Path(os.environ.get('DJANGO_SQLITE_PATH', BASE_DIR / 'db.sqlite3')),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = Path(os.environ.get('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles'))

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', BASE_DIR / 'media'))
FILE_UPLOAD_TEMP_DIR = os.environ.get('DJANGO_UPLOAD_TEMP_DIR')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'blog.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_THROTTLE_RATES': {
        'contact': '5/hour',
        'comment': '10/hour',
        'newsletter': '5/hour',
        # Confirm and unsubscribe links carry unguessable tokens, so this only
        # stops hammering. It stays generous because mail providers send
        # one-click unsubscribes for many readers from a few shared addresses.
        'newsletter-token': '60/minute',
    },
    # nginx appends the real peer address to X-Forwarded-For, so the last entry
    # is the only one a client cannot spoof. Without this, DRF hashes the whole
    # header and a caller can dodge the rate limit by sending their own.
    'NUM_PROXIES': 1,
}

# Throttle counters live in the cache. The default per-process backend would give
# each of the gunicorn workers its own tally, letting through one limit per
# worker, so the cache has to be shared. The database avoids running anything new
# alongside the app; `manage.py createcachetable` provisions it.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'blog_cache_table',
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'DJANGO_CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000',
    ).split(',')
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG)
SESSION_COOKIE_SECURE = env_bool('DJANGO_SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('DJANGO_CSRF_COOKIE_SECURE', not DEBUG)
SECURE_HSTS_SECONDS = int(
    os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0')
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
SECURE_HSTS_PRELOAD = env_bool('DJANGO_SECURE_HSTS_PRELOAD', False)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
    },
}

# Email. With no SMTP host configured, mail is printed to the console instead of
# sent, which is what local development wants.
SITE_NAME = os.environ.get('SITE_NAME', 'wh1t3r4v3n')
# Public address of the frontend, used to build the links inside emails.
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:5173').rstrip('/')

EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('DJANGO_EMAIL_USE_TLS', True)
# A stalled SMTP server would otherwise hold a gunicorn worker indefinitely.
EMAIL_TIMEOUT = int(os.environ.get('DJANGO_EMAIL_TIMEOUT', '15'))
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', f'{SITE_NAME} <noreply@localhost>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Where contact-form messages are forwarded. Empty means they are only stored.
CONTACT_NOTIFY_EMAIL = os.environ.get('CONTACT_NOTIFY_EMAIL', '')

# Brevo's free plan allows 300 emails a day. New-post mail stops at this many per
# rolling 24 hours and picks up where it left off on a later run, leaving room
# for confirmation and contact emails.
NEWSLETTER_DAILY_SEND_LIMIT = int(os.environ.get('NEWSLETTER_DAILY_SEND_LIMIT', '250'))
# Caps confirmation emails across all sign-ups, so a botnet cycling through
# addresses cannot spend the sending quota or the domain's reputation.
NEWSLETTER_CONFIRMATIONS_PER_HOUR = int(os.environ.get('NEWSLETTER_CONFIRMATIONS_PER_HOUR', '30'))
NEWSLETTER_CONFIRMATION_COOLDOWN = timedelta(minutes=15)
NEWSLETTER_CONFIRMATION_MAX_AGE = timedelta(days=3)
# Posts published longer ago than this are never mailed out, so turning email on
# late, or republishing an old post, cannot surprise every subscriber.
NEWSLETTER_MAX_POST_AGE = timedelta(days=7)
