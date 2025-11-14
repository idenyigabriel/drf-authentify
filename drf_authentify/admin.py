from django.db.models import Q
from django.contrib import admin
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from drf_authentify.models import get_token_model
from drf_authentify.forms import AuthTokenAdminForm


AuthToken = get_token_model()


class ExpirationStatusFilter(admin.SimpleListFilter):
    title = _("Expiration Status")
    parameter_name = "expiration"

    def lookups(self, request, model_admin):
        return [("valid", _("Valid")), ("expired", _("Expired"))]

    def queryset(self, request, queryset):
        now = timezone.now()
        value = self.value()

        if value == "valid":
            return queryset.filter(Q(expires_at__gt=now) | Q(expires_at__isnull=True))
        elif value == "expired":
            return queryset.filter(expires_at__lt=now)
        return queryset


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    form = AuthTokenAdminForm
    list_filter = (ExpirationStatusFilter, "created_at")
    search_fields = ("user__" + get_user_model().USERNAME_FIELD,)
    readonly_fields = ("token", "refresh_token", "last_refreshed_at")
    list_display = ["user", "auth_type", "is_valid", "expires_at", "created_at"]

    def is_valid(self, obj):
        return not obj.is_expired

    is_valid.boolean = True
    is_valid.short_description = _("Valid")
