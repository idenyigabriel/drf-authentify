# DRF Authentify

[![Build Status](https://github.com/idenyigabriel/drf-authentify/actions/workflows/test.yml/badge.svg)](https://github.com/idenyigabriel/drf-authentify/actions/workflows/test.yml)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

**[drf-authentify](https://github.com/idenyigabriel/drf-authentify)** is a near drop-in replacement for Django REST Framework’s default token authentication—except better.


---
## 🚀 Why Use `drf-authentify`?

Compared to the default DRF token system, `drf-authentify` offers several key improvements:

- 🔑 **Multiple tokens per user**
- 🔐 **Enhanced security** with contextual access validation
- ⚙️ **Utility methods** for creating, revoking, and managing tokens
- 🧩 **Unopinionated design**—integrate it your way

It is built to be simple, extensible, and flexible enough to meet modern authentication needs.

---
## 📦 Requirements

- Python ≥ 3.8  
- Django ≥ 3.2  
- Django REST Framework ≥ 3.0

---
## ⚙️ Installation

Install via pip:

```bash
pip install drf-authentify
```

Add it to your INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # your existing apps...
    'drf_authentify',
]
```
Run migrations:

```bash
python manage.py migrate
```
Once installed, a new AuthToken model will appear in your Django admin for token management.

---
## ⚙️ Global Configuration

Customize behavior in settings.py using the DRF_AUTHENTIFY config:

```python
DRF_AUTHENTIFY = {
    "COOKIE_KEY": "token", 
    "ALLOWED_HEADER_PREFIXES": ["bearer", "token"],
    "TOKEN_EXPIRATION": 3000,
    "ENABLE_AUTH_RESTRICTION": False,
    "STRICT_CONTEXT_PARAMS_ACCESS": False,
}
```

### Setting Descriptions

- COOKIE_KEY: Key name used to retrieve tokens from cookies.
- ALLOWED_HEADER_PREFIXES: Acceptable prefixes for the Authorization header.
- TOKEN_EXPIRATION: Default expiration time (in seconds) for new tokens.
- ENABLE_AUTH_RESTRICTION: Restricts a token to only its creation channel (header/cookie).
- STRICT_CONTEXT_PARAMS_ACCESS: Enforces error raising on undefined context_obj keys.

> **Note:**
> ⚠️ Don’t forget to allow any custom header prefixes in your CORS settings to avoid CORS errors.

---
## 🔐 Creating Tokens

Use utility methods from TokenService:

```python
from drf_authentify.services import TokenService

# Header-based token
token = TokenService.generate_header_token(user, context=None, expires=3000)

# Cookie-based token
token = TokenService.generate_cookie_token(user, context=None, expires=3000)
```

### Contextual Tokens

You can optionally attach a context dictionary to any token and customize its expiration using the expires parameter. If not set, the default global TOKEN_EXPIRATION is used.

> **Note:**
> If `ENABLE_AUTH_RESTRICTION` is True, a token created for cookie use cannot be used in a header and vice versa.

---
## 🧹 Revoking Tokens

You can revoke tokens in several ways:

```python
from drf_authentify.services import TokenService

# Revoke token tied to the current request
TokenService.revoke_token_from_request(request)

# Revoke all tokens for the user in the request
TokenService.revoke_all_tokens_for_user_from_request(request)

# Revoke all tokens for a specific user
TokenService.revoke_all_user_tokens(request.user)

# Revoke all expired tokens (useful for cleanup)
TokenService.revoke_expired_tokens()
```

---
## 🛡️ Authentication Classes

drf-authentify provides two authentication classes:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'drf_authentify.auth.CookieAuthentication',
        'drf_authentify.auth.AuthorizationHeaderAuthentication',
    ]
}
```
These can be used globally or at the view level.

---
## 🔍 Accessing the Current Token and Context

Inside an authenticated view:

```python
def sample_view(request):
    user = request.user            # Authenticated user
    token = request.auth           # AuthToken instance
    context = token.context        # Context dictionary
    scope = token.context_obj      # Access as object
```