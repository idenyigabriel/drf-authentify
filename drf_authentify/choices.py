from django.db import models
from django.utils.translation import gettext_lazy as _


class AUTH(models.TextChoices):
    TOKEN = "token", _("token")
    COOKIE = "cookie", _("cookie")
