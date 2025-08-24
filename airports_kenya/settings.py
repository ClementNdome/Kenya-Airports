from pathlib import Path
import os
from decouple import config
import dj_database_url  # <-- Add this line

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key secret!
SECRET_KEY = config("SECRET_KEY")  # <-- Read from .env

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config('DEBUG', default=False, cast=bool)  # <-- Read from .env
DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")  # <-- Read from .env
ALLOWED_HOSTS = ["*"]



# enable this while working locally and ensure it is commnented while pushing to production
# Configure GDAL (for Windows)
# if os.name == 'nt':  # Only for Windows
#     # Path to your GDAL DLL (adjust version if needed)
#     GDAL_LIBRARY_PATH = r'C:\OSGeo4W\bin\gdal310.dll'
    
#     # Optional: Set other GDAL environment variables
#     OSGEO4W_PATH = r'C:\OSGeo4W'
#     os.environ['OSGEO4W_ROOT'] = OSGEO4W_PATH
#     os.environ['GDAL_DATA'] = os.path.join(OSGEO4W_PATH, 'share', 'gdal')
#     os.environ['PROJ_LIB'] = os.path.join(OSGEO4W_PATH, 'share', 'proj')
#     os.environ['PATH'] = OSGEO4W_PATH + r'\bin;' + os.environ['PATH']

# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.gis",  # GeoDjango support
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "airports_strips",
    "leaflet",
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






DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": config("DB_NAME", default="airports_db"),
        "USER": config("DB_USER", default="avnadmin"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432", cast=int),
        "OPTIONS": {
            "sslmode": config("DB_SSLMODE", default="require"),
        },
    }
}

# Optional: Add database URL support as fallback
DATABASE_URL = config("DATABASE_URL", default=None)
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.parse(
        DATABASE_URL,
        engine="django.contrib.gis.db.backends.postgis",
        conn_max_age=600,
    )

# local database for local testing
# DATABASES = {
#     "default": {
#         "ENGINE": "django.contrib.gis.db.backends.postgis",
#         "NAME": "airports",
#         "USER": "postgres",
#         "HOST": "localhost",
#         "PASSWORD": "0323",
#         "PORT": "5432",
#     }
# }


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


# GDAL_LIBRARY_PATH = os.environ.get("GDAL_LIBRARY_PATH", "C:/OSGeo4W/bin/gdal310.dll")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Leaflet configuration
LEAFLET_CONFIG = {
    "DEFAULT_CENTER": (-0.0236, 37.9062),  # Center of Kenya
    "DEFAULT_ZOOM": 6,
    "MIN_ZOOM": 3,
    "MAX_ZOOM": 18,
    "SCALE": "both",
    "ATTRIBUTION_PREFIX": "Kenya Airports GIS",
}

STATIC_ROOT = BASE_DIR / "staticfiles"

# JAZZMIN
JAZZMIN_SETTINGS = {
    # Title on the brand (19 chars max)
    "site_title": "kenya airports Admin",
    # Title on the login screen (19 chars max)
    "site_header": "kenya airports",
    # Logo to use for your site
    # "site_logo": "images/logo.png",  # Path to your logo (in static files)
    # Welcome text on the login screen
    "welcome_sign": "Welcome to the Kenya Airports GIS Admin Panel",
    # Copyright on the footer
    "copyright": "kenya airports-clm webgis",
    # Custom icons for models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "gis_system.YourModel": "fas fa-tree",  # Example for a custom model
    },
    # Customize the admin panel colors
    "theme": "dark",  # Options: "light", "dark", "slate", "lux", "cosmo", "flatly"
    # Show/hide UI elements
    "show_ui_builder": True,  # Enable the UI customizer
    # Custom links to add to the admin panel
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "site", "url": "admin:index", "permissions": ["auth.view_user"]},
        {
            "name": "Support",
            "url": "https://github.com/farridav/django-jazzmin/issues",
            "new_window": True,
        },
    ],
    # Customize the order of apps and models
    "order_with_respect_to": [
        "gis_system",  # Your app
        "auth",  # Authentication app
    ],
}
