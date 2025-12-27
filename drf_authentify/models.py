from django.apps import apps
from django.utils.module_loading import import_string

from drf_authentify.compat import Type
from drf_authentify.settings import authentify_settings
from drf_authentify.base.models import AbstractAuthToken



# Type alias for token model
TokenType = Type["AuthToken"]


def get_token_model() -> TokenType:
    """
    Return the current swappable AuthToken model class.
    Resolves only when called.
    """
    model_path = authentify_settings.TOKEN_MODEL
    if "." in model_path:
        app_label, model_name = model_path.rsplit(".", 1)
        return apps.get_model(app_label, model_name)
    # This path is usually not used for swappable models, but maintained for compatibility
    return import_string(model_path)



class AuthToken(AbstractAuthToken):
    class Meta(AbstractAuthToken.Meta):
        swappable = "drf_authentify.AuthToken"
