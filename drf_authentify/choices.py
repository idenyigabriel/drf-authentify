from django.db import models
from django.utils.translation import gettext_lazy as _


class AUTH_TYPES(models.TextChoices):
    HEADER = "header", _("Header")
    COOKIE = "cookie", _("Cookie")
