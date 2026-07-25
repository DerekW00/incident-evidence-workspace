import os

SECRET_KEY = os.environ.get("SECRET_KEY", "synthetic-local-only-key")
DEBUG = os.environ.get("DEMO_MODE") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "investigations",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE", "incident_evidence"),
        "USER": "dw",
        "HOST": os.environ.get(
            "PGHOST", "/Users/dw/code/portfolio-python/.runtime/pg16/incident/socket"
        ),
        "PORT": "15533",
    }
}
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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
                "django.template.context_processors.csrf",
            ]
        },
    }
]
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login/"

DEMO_MODE = os.environ.get("DEMO_MODE") == "1"
LOGIN_REDIRECT_URL = "/"

TIME_ZONE = "UTC"
