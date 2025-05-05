from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_authentify.models import AuthToken


class ExpirationStatusFilter(admin.SimpleListFilter):
    title = _("Expiration Status")
    parameter_name = "expiration"

    def lookups(self, *args, **kwargs):
        return [("valid", _("Valid")), ("expired", _("Expired"))]

    def queryset(self, request, queryset):
        now = timezone.now()
        value = self.value()

        if value == "valid":
            return queryset.filter(expires_at__gt=now)
        elif value == "expired":
            return queryset.filter(expires_at__lt=now)
        return queryset


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    model = AuthToken
    list_display = [
        "token",
        "user",
        "auth_type",
        "valid",
        "expires_at",
        "created_at",
    ]
    list_filter = (ExpirationStatusFilter, "created_at")

    def valid(self, obj):
        return timezone.now() < obj.expires_at

    valid.boolean = True
