"""SimpleUI startup integration, following the teaching project's setup."""

from django.conf import settings
from simpleui.apps import SimpleApp


class LabSimpleUIConfig(SimpleApp):
    name = "simpleui"

    def ready(self):
        super().ready()
        # SimpleUI removes this middleware for its iframe tabs. Restore it and
        # use SAMEORIGIN in settings so only this site's own tabs can embed pages.
        protection = "django.middleware.clickjacking.XFrameOptionsMiddleware"
        if protection not in settings.MIDDLEWARE:
            settings.MIDDLEWARE = [*settings.MIDDLEWARE, protection]
