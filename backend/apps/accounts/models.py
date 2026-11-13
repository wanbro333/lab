from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Keep an extensible user model from the first migration."""

    display_name = models.CharField("显示名称", max_length=80, blank=True)

    def __str__(self):
        return self.display_name or self.username
