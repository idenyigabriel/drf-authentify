from django.db.models import Q
from django.contrib import admin
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.sites import AlreadyRegistered

from drf_authentify.models import get_token_model
from drf_authentify.forms import AuthTokenAdminForm
from drf_authentify.utils.tokens import generate_access_token, generate_refresh_token


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


class AuthTokenAdmin(admin.ModelAdmin):
    form = AuthTokenAdminForm
    raw_id_fields = ("user",)
    list_filter = (ExpirationStatusFilter, "created_at")
    search_fields = (f"user__{get_user_model().USERNAME_FIELD}",)
    readonly_fields = ("access_token_hash", "refresh_token_hash", "last_refreshed_at")
    list_display = [
        "user",
        "auth_type",
        "is_valid",
        "expires_at",
        "refresh_until",
        "created_at",
    ]

    def is_valid(self, obj):
        return not obj.is_expired

    is_valid.boolean = True
    is_valid.short_description = _("Valid")

    def save_model(self, request, obj, form, change):
        if not change:
            raw_token, hashed_token = generate_access_token()
            obj.access_token_hash = hashed_token

            raw_refresh = None
            if obj.refresh_until:
                raw_refresh, hashed_refresh = generate_refresh_token()
                obj.refresh_token_hash = hashed_refresh

            self.message_user(request, f"🗝 Access Token:\n{raw_token}")
            if raw_refresh:
                self.message_user(request, f"🔄 Refresh Token:\n{raw_refresh}")

        return super().save_model(request, obj, form, change)


def register_token_admin():
    AuthToken = get_token_model()

    try:
        admin.site.register(AuthToken, AuthTokenAdmin)
    except AlreadyRegistered:
        pass


register_token_admin()
