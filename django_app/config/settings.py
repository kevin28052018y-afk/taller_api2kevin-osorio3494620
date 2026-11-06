"""
Settings del proyecto (versión para Render).
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Básicos (se configuran con variables de entorno en Render) ---
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-solo-para-desarrollo")
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = [".onrender.com", ".vercel.app", "localhost", "127.0.0.1"]
# Render define esta variable con el dominio exacto de tu servicio
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com", "https://*.vercel.app"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Aplicación ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # sirve los estáticos en Render
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos (WhiteNoise) ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# --- Conexión con la API FastAPI y sesiones ---
# En Render define API_URL con la URL de tu API, ej: https://mi-api.onrender.com
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000").rstrip("/")

# La sesión (donde se guarda el JWT) dura lo mismo que el token: 1 hora
SESSION_COOKIE_AGE = 60 * 60
SESSION_COOKIE_HTTPONLY = True
# Sesiones en cookie firmada (no necesita escribir en la base de datos)
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_SECURE = not DEBUG

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
