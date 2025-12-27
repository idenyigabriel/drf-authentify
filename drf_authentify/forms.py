from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from drf_authentify.models import get_token_model


AuthToken = get_token_model()


class AuthTokenAdminForm(forms.ModelForm):
    class Meta:
        model = AuthToken
        fields = "__all__"
        exclude = ("access_token_hash", "refresh_token_hash", "last_refreshed_at")

    def clean(self) -> dict:
        cleaned_data = super().clean()

        expires_at = cleaned_data.get("expires_at")
        refresh_until = cleaned_data.get("refresh_until")

        if expires_at and refresh_until and expires_at > refresh_until:
            raise ValidationError(
                {
                    "refresh_until": [_("Must be on or after expires_at")],
                    "expires_at": [_("Must be on or before refresh_until")],
                }
            )

        return cleaned_data
