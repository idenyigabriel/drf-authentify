## 0.3.9

Fixes:
- Fix error in Auth class' authentication_header method.

## 0.3.8

Features:
- Add new setting configuration "ENABLE_AUTH_RESTRICTION" to allow users enable/disable channel restrictions.

Fixes:
- Auth classes no longer raise errors on failure, this function will now be left to DRF permission classes.
- Update AuthToken private method __generate_token to return token string not token instance.

## 0.3.7

Fixes:
- Token auth class checking wrong condition in authenticate_header method.

## 0.3.6

Fixes:
- auth class accessing wrong method
- update authenticate_header on auth classes

## 0.3.5

Docs
- update documentation

Fixes:
- auth class accessing invalid variable

## 0.3.4

Fixes
- documentation urls on pyproject.toml
- changelog urls on pyproject.toml

## 0.3.0

Beta Release