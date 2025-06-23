import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# --- DEBUGGING START ---
# This line is added to confirm if this specific settings.py file is being loaded.
print("--- Loading mylendingapp.settings ---")
path = '/home/kintu2388/django-loanweb3'
# --- DEBUGGING END ---

# Load environment variables from .env file at the very top
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core Django Settings ---

# SECURITY WARNING: keep the secret key used in production secret!
# Use a strong, randomly generated key in production, set via environment variable.
# For example: python -c 'import secrets; print(secrets.token_urlsafe(50))'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-insecure-default-key-for-dev-only-CHANGE-ME-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
# Set DEBUG to False in production. Control with environment variable.
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True' # Default to True for local development

# Allowed hosts for your Django application.
# In production, this *must* include your PythonAnywhere domain (e.g., 'yourusername.pythonanywhere.com')
# and any other domains you might be serving from.
# For local development, '127.0.0.1' and 'localhost' are included.
# It's recommended to parse from an environment variable for production.
ALLOWED_HOSTS_STR = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]

# --- Third-party Service URLs (from .env) ---
WEB3_PROVIDER_URL = os.getenv('WEB3_PROVIDER_URL')
LOAN_MANAGER_ADDRESS = os.getenv('LOAN_MANAGER_ADDRESS')

# --- Application Definition ---

INSTALLED_APPS = [
    'jazzmin', # Django Jazzmin for enhanced admin interface
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST Framework and JWT
    'rest_framework',
    'rest_framework_simplejwt', # Simple JWT for token-based authentication
    'corsheaders',              # For handling CORS (Cross-Origin Resource Sharing)

    # Your custom apps
    'users',
    'loans',
    'wallet',
    'kyc',
    # Add any other custom apps here
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS middleware should be high up
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mylendingapp.urls' # Ensure this matches your project's root URL file

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # You can add global template directories here if needed
        'APP_DIRS': True, # Looks for 'templates' directory inside each app
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

WSGI_APPLICATION = 'mylendingapp.wsgi.application' # Ensure this points to your project's WSGI file

# --- Database Configuration ---
# Use SQLite for development. For production on PythonAnywhere, it's generally fine for small
# projects, but for larger apps, consider a separate database service and use `dj-database-url`
# to parse a DATABASE_URL environment variable.
# Example using dj-database-url (install with `pip install dj-database-url`):
# import dj_database_url
# DATABASES = {
#     'default': dj_database_url.parse(os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3'))
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# --- Internationalization and Time Zones ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static and Media Files Configuration ---
# URL prefix for static files.
STATIC_URL = 'static/'

# The absolute path to the directory where collectstatic will gather static files for deployment.
# This directory will be served by PythonAnywhere as your static files.
STATIC_ROOT = BASE_DIR / 'staticfiles' # Changed to 'staticfiles' for common convention

# Configuration for user-uploaded media files (if applicable)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Custom User Model ---
AUTH_USER_MODEL = 'users.User' # Specify your custom user model

# --- Django REST Framework Settings ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Use JWTAuthentication for token-based authentication with Simple JWT
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Default to requiring authentication for all views unless explicitly overridden
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [ # Basic rate limiting to prevent abuse
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day', # 100 requests per day for unauthenticated users
        'user': '1000/day' # 1000 requests per day for authenticated users
    },
    # Optional: Renderer for browsable API
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    #     'rest_framework.renderers.BrowsableAPIRenderer',
    # )
}

# --- SIMPLE JWT Configuration ---
# Configure token lifetimes, algorithms, and header types.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),       # How long access tokens are valid
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),         # How long refresh tokens are valid
    'ROTATE_REFRESH_TOKENS': False,                      # Whether refresh tokens rotate upon use
    'BLACKLIST_AFTER_ROTATION': False,                   # Whether old refresh tokens are blacklisted
    'UPDATE_LAST_LOGIN': False,                          # Update user's last login time

    'ALGORITHM': 'HS256',                                # Hashing algorithm for tokens
    'SIGNING_KEY': SECRET_KEY,                           # Uses your Django SECRET_KEY for signing
    'VERIFYING_KEY': None,                               # Not typically needed for symmetric keys
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',), # <--- CRUCIAL: This must match what your client (e.g., Flutter) sends
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION', # Standard header name
    'USER_ID_FIELD': 'id',                       # Field to identify the user in the token payload
    'USER_ID_CLAIM': 'user_id',                  # Claim name for the user ID
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti', # JWT ID claim for blacklisting

    # Sliding token settings (if you choose to use sliding tokens)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# --- CORS Headers Configuration ---
# SECURITY WARNING: In production, do NOT use CORS_ALLOW_ALL_ORIGINS = True.
# Instead, explicitly list your frontend's origins in CORS_ALLOWED_ORIGINS.
CORS_ALLOW_ALL_ORIGINS = DEBUG # Allow all origins only in DEBUG mode (local development)
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",             # Example: React/Vue/Angular dev server
#     "http://127.0.0.1:8000",             # Django dev server
#     "http://localhost:53041",            # Example: Flutter web dev port (check your Flutter run output)
#     "https://yourusername.pythonanywhere.com", # Your PythonAnywhere domain in production
#     "https://www.yourdomain.com",        # Your custom domain if you have one
# ]

# --- Production Security Settings (Enabled when DEBUG is False) ---
if not DEBUG:
    # Forces all connections to be HTTPS. Set up SSL on PythonAnywhere.
    # SECURE_SSL_REDIRECT = True # Uncomment if you're sure about HTTPS redirect
    
    # Prevents XSS attacks by filtering certain characters.
    SECURE_BROWSER_XSS_FILTER = True
    
    # Prevents MIME sniffing attacks.
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # Prevents clickjacking attacks by limiting where the page can be embedded in a frame.
    X_FRAME_OPTIONS = 'DENY'
    
    # HTTP Strict Transport Security (HSTS) settings.
    # Tells browsers to always use HTTPS for your domain for a specified duration.
    # Only enable after your site is fully on HTTPS.
    SECURE_HSTS_SECONDS = 31536000 # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True # Apply to Google's HSTS preload list (requires specific checks)
    
    # Controls the Referrer-Policy header, limiting what referrer information is sent.
    SECURE_REFERRER_POLICY = 'same-origin'
    
    # Set this to True in production if your site is always served via HTTPS.
    # This helps Django know if the request is secure.
    # For PythonAnywhere, you might need to configure their web app to forward the X-Forwarded-Proto header.
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- Debugging: Print resolved paths and settings to console ---
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"BASE_DIR: {BASE_DIR}")
print(f"STATIC_ROOT: {STATIC_ROOT}")
print(f"MEDIA_ROOT: {MEDIA_ROOT}")
