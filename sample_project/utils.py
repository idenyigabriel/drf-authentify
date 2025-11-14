from rest_framework.response import Response


def set_cookie(response: Response, token: str, duration: int = 3600) -> Response:
    cookie = dict()
    cookie["value"] = token
    cookie["path"] = "/"
    cookie["samesite"] = "Lax"
    cookie["max_age"] = duration
    cookie["secure"] = False
    cookie["httponly"] = False
    cookie["domain"] = None
    response.set_cookie("token", **cookie)
    return response
