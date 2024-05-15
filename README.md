# DRF Authentify Documentation

<br />

[![Build Status](https://github.com/idenyigabriel/drf-authentify/actions/workflows/test.yml/badge.svg)](https://github.com/idenyigabriel/drf-authentify/actions/workflows/test.yml)
<br/>

[drf-authentify](https://github.com/idenyigabriel/drf-authentify) is a near splitting replica of the simple django rest framework default token system, except better.

The major difference between `django rest framework` default token and `drf-authentify` are:

- `drf-authentify` allows multiple tokens per users
- `drf-authentify` adds extra security layer by using access validation
- bonus: drf-authentify provides utility methods to handle common use cases.

drf authentify aims to be as simple as possible, while providing a great set of features to meet your authentication demands without enforcing a certain pattern to your application flow.


## Requirements

- Python >=3.8
- Django >=3.2
- djangorestframework 3


## Installation

Installation is easy using `pip` and will install all required libraries

```python
$ pip install drf-authentify
```

Then add the `drf-authentify` to your project by including the app to your `INSTALLED_APPS`.

The app should preferably go somewhere after your regular apps.

```python
INSTALLED_APPS = (
    ...
    'drf_authentify'
)
```

`drf-authentify` adds a model to your admin section called AuthToken, with this you can view and manage all tokens created on your applications. We already have a nice setup for you on django admin section.

Finally migrate all database entries.

```
$ python3 manage.py migrate
```


## Global Configuration

For a one type fits all case, you can globally alter the following settings, or leave the default as it is.

```python
DRF_AUTHENTIFY = {
    "ALLOWED_HEADER_PREFIXES": ["bearer", "token"] # default
    "TOKEN_EXPIRATION": 3000 # default
    "COOKIE_KEY": "token" # default
}
```

## Customizing Tokens

- ALLOWED_HEADER_PREFIXES: Here you can provide a list of prefixes that are allowed for your authentication header. We will validate this when you apply our authentication scheme `drf_authentify.auth.TokenAuthentication` as shown below.

- COOKIE_KEY: With this, you can customize what key we should use to retrieve your authentication cookie frmo each request. We will also validate this when you apply our authentication scheme `drf_authentify.auth.CookieAuthentication` as shown below.

- TOKEN_EXPIRATION: With this you can globally set the duration of each token generated, this can also be set per view, as you would see below.

> **Note:**
> Do not forget to add custom header prefixes to your cors-header as this could cause cors errors.


## Creating Tokens

Two utility methods have been provided for you to leverage for creating or generating user tokens on `drf-authentify`. For ease, they are attached to the AuthToken model class.

```python
from drf_authentify.models import AuthToken

def sample_view(request, *arg, **kwargs):
    token = AuthToken.generate_cookie_token(user, context=None, expires=3000)

def sample_view(request, *arg, **kwargs):
    token = AuthToken.generate_header_token(user, context=None, expires=3000)

```

`drf-authentify` allows you to save contexts alongside your tokens if you need to, also feel free to alter the duration of a token validity using the expires parameters, we'll use the globally set `TOKEN_EXPIRATION` or default if none is provided.


## Deleting Tokens

To delete tokens, simply use one of the three utility methods provides on the AuthToken class.

```python
from drf_authentify.utils import clear_request_tokens, delete_request_token, clear_expired_tokens, clear_user_tokens

# Remove single token based on request authenticated user
delete_request_token(request) 

# Remove all user tokens based on request authenticated user
clear_request_tokens(request) 

# Remove all tokens for user
clear_user_tokens(user) 

# Remove all expired tokens
clear_expired_tokens()
```


## Authentication Schemes

drf authentify provides you with two authentication classes to cover for both broad type of tokens you can generate. These are very import in django rest framework, and can be used either globally or per view.

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'drf_authentify.auth.CookieAuthentication',
        'drf_authentify.auth.TokenAuthentication',
    ]
}
```

By adding this, you can appriopriately check for authentication status and return the user on the request object.

> **Note:**
> For convenience, you can access the current token object in your authenticated view through request.auth, this would allow easy access context which can be used to store authorization scope and other important data.