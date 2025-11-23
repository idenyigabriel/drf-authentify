from dataclasses import dataclass

from drf_authentify.compat import TYPE_CHECKING

if TYPE_CHECKING:
    from drf_authentify.models import TokenType


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    token_instance: "TokenType"
