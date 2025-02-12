from pathlib import Path
import os
from decouple import config 
import dj_database_url # <-- Add this line

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key secret!
SECRET_KEY = config('SECRET_KEY')  # <-- Read from .env

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config('DEBUG', default=False, cast=bool)  # <-- Read from .env
DEBUG= True
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')  # <-- Read from .env
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.gis',  # GeoDjango support
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'airports_strips',
    'leaflet',
    # 'airports_strips',
    
    # 'djangorestframework-gis',
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ROOT_URLCONF = "GIS.urls"
ROOT_URLCONF = "airports_kenya.urls"


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
            ],
        },
    },
]
# WSGI_APPLICATION = "GIS.wsgi.application"
WSGI_APPLICATION = "airports_kenya.wsgi.application"
# Database configuration (using dj_database_url)
DATABASE_URL = config(
    'DATABASE_URL',
    default='postgresql://airports_628w_user:kT2Hy7DSDYcC5fCAUNBdO2EUVDaH3X7n@dpg-cumdmuggph6c73dfp4cg-a.oregon-postgres.render.com/airports_628w'
)

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, engine='django.contrib.gis.db.backends.postgis')
}
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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field


GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH', 'C:/OSGeo4W/bin/gdal310.dll')

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Leaflet configuration
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (-0.0236, 37.9062),  # Center of Kenya
    'DEFAULT_ZOOM': 6,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'SCALE': 'both',
    'ATTRIBUTION_PREFIX': 'Kenya Airports GIS'
}

STATIC_ROOT = BASE_DIR / "staticfiles"