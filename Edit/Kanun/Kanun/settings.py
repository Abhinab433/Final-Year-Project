import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure proper session and security cookie settings for development
SESSION_COOKIE_SECURE = False  # Disable for local development
CSRF_COOKIE_SECURE = False  # Disable for local development
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Retrieve environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "")

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-#default-secret-key")  # Use a default key for local testing
DEBUG = True

ALLOWED_HOSTS = ['*','localhost','127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chat',
    'dashboard',
    'accounts',
    'injestion',  # Ensure this app is actually needed
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'Kanun.middleware.AuthRequiredMiddleware',  # Ensure this is implemented correctly
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Kanun.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "Kanun/templates"],
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

WSGI_APPLICATION = 'Kanun.wsgi.application'

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 3600
SESSION_SAVE_EVERY_REQUEST = True

# Static files settings
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Ensure this directory exists
]
STATIC_ROOT = BASE_DIR / 'collected_static'  # Set the collection point for static files

MEDIA_URL = '/mediafiles/'
MEDIA_ROOT = BASE_DIR / 'static/mediafiles'

# Authentication and User Model Settings
AUTH_USER_MODEL = 'accounts.CustomUser'

LOGIN_REDIRECT_URL = '/cover.html'
LOGOUT_REDIRECT_URL = '/login/'

