from django import forms
from django.utils import timezone
from drf_authentify.models import get_token_model
from drf_authentify.utils import generate_token


AuthToken = get_token_model()


class AuthTokenAdminForm(forms.ModelForm):
    """
    Admin form for creating AuthToken instances.
    Generates token and refresh_token automatically.
    """

    class Meta:
        model = AuthToken
        fields = [
            "auth_type",
            "user",
            "context",
            "expires_at",
            "refresh_until",
            "last_refreshed_at",
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)

        is_new = instance.pk is None

        raw_token = None
        raw_refresh_token = None

        if is_new:
            # Generate main token
            raw_token, hashed_token = generate_token()
            instance.token = hashed_token

            # Generate refresh token if refresh_until is set
            if instance.refresh_until:
                raw_refresh_token, hashed_refresh_token = generate_token()
                instance.refresh_token = hashed_refresh_token

            # Default last_refreshed_at to now
            if not instance.last_refreshed_at:
                instance.last_refreshed_at = timezone.now()

        if commit:
            instance.save()

        # Attach raw token values for admin feedback
        self.raw_token = raw_token
        self.raw_refresh_token = raw_refresh_token

        return instance
