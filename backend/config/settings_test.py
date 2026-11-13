"""Fast unit tests only; the default application always uses MySQL."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "isolated-unit-test-key-not-for-deployment")
from .settings import *  # noqa: F403,E402

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
