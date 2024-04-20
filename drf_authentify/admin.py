from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_authentify.models import AuthToken


class ValidListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("expiration")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "lifetime"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("valid", _("valid")),
            ("expired", _("expired")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == "valid":
            return queryset.filter(expires_at__gt=timezone.now())
        if self.value() == "expired":
            return queryset.filter(expires_at__lt=timezone.now())


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    model = AuthToken
    list_display = [
        "token",
        "user",
        "auth",
        "valid",
        "expires_at",
        "created_at",
    ]
    list_filter = (ValidListFilter, "created_at")

    def valid(self, obj):
        return timezone.now() < obj.expires_at

    valid.boolean = True
