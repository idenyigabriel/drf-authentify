from django.db import models
from django.utils.translation import gettext_lazy as _


class AUTHTYPE_CHOICES(models.TextChoices):
    HEADER = "header", _("Header")
    COOKIE = "cookie", _("Cookie")
