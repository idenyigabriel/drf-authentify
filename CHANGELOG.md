## [0.6.2] - 2025-12-27

### Change
- Decouple AuthToken: Removed the user reverse relationship to enforce direct model filtering and prevent architectural leaks.
- Restructure: Moved AbstractAuthToken to base/models for a more logical project hierarchy.
- Admin Update: Switched admin form fields to __all__ to automatically capture inherited fields from the User model.

## [0.6.1] - 2025-11-23

### Change
- Update pyproject classifiers

## [0.6.0] - 2025-11-23

### Added
- Tests added
- Update docs reflecting new changes

### Change
- Optimizations and modifications to several logics.
- Renamed model fields token to access_token_hash, and refresh_token to refresh_token_hash
- Return newly created access and refresh token in messages when done through django admin.

## [0.5.8] - 2025-11-20

### Change
- Auth class should return user and token from post handlers and refresh handler, incase of modifications.

## [0.5.7] - 2025-11-14

### Change
- TokenService method refresh_token not formatting custom value expires_in properly before calling generate token internal utility method.

## [0.5.6] - 2025-11-14

### Change
- TokenService method revoke_token now correctly takes token (can be retrieved from request.auth in views) instead of token_str which is only available after token is created.

## [0.5.5] - 2025-11-14

### Added
- added post_auto_refresh_handler to allow post refresh custom actions without having to overhaul the entire authentication

### Change
- drop support for django 3.2
- post_auth_handler and newly added post_auto_refresh_handler now take user, token and token string and return a tuple of user and token to allow for modifications on user or token returned for custom cases.

## [0.5.4] - 2025-11-14

### Change
- drop support for django 3.2

## [0.5.3] - 2025-11-14

### Change
- drop support for python version 3.8

## [0.5.2] - 2025-11-14

### Change
- improve compatibility with older python version, use Union over newer syntax |
- remove library coverage as it seems to have some issues with python 3.9, alternative or different version will be added in future.

## [0.5.1] - 2025-11-14

### Change
- Add compatibility for older python versions for typehinting, older version will use typing_extensions, and newer versions will use typing standard module.


## [0.5] - 2025-11-14

### Added
- Full project update
- New features include AUTH_REFRESH, REFRESH_TOKEN, etc.

### Changed
- Introduced breaking changes with new version expected to be moved to stable v1.0 after testing.
- Updated models to reflect new changes.

### Expected
- Invalidated all project tests, new tests will added shortly.


## [0.4] - 2025-05-05

### Changed
- Renamed `AUTH` to `AUTHTYPE_CHOICES` for improved clarity.
- Updated `AUTHTYPE_CHOICES` values from `'token'` and `'cookie'` to `'header'` and `'cookie'`.
- Renamed `_context` field (a `TextField`) to `context` and changed its type to `JSONField`.

### Added
- dropped support for python 3.7
- Introduced `TokenService` class and moved token generation and revocation logic out of the `AuthModel`.
- Added `context_obj` property to allow dot-notation access to context data.
- Added `as_dict()` method to convert context to a dictionary.
- Added validation for the `context` field.
- Added additional test cases to improve test coverage and robustness.
- Added `STRICT_CONTEXT_PARAMS_ACCESS` setting to handle whether or not to raise an error when unexisting context param is accessed via context_obj property.

### Docs
- Updated documentation.


## [0.3.11]

### Fixed
- Fixed issue with non-existing document on PyPI.


## [0.3.10]

### Fixed
- Fixed error in `TokenAuthentication.authenticate` method (was not updated after `authentication_header` method was changed).


## [0.3.9]

### Fixed
- Fixed error in `Auth.authentication_header` method.


## [0.3.8]

### Added
- Added `ENABLE_AUTH_RESTRICTION` setting to allow users to enable or disable channel restrictions.

### Fixed
- Auth classes no longer raise errors on failure; responsibility is now delegated to DRF permission classes.
- Updated `AuthToken.__generate_token()` to return token string instead of token instance.


## [0.3.7]

### Fixed
- Fixed condition check in `authenticate_header` method of token auth class.


## [0.3.6]

### Fixed
- Fixed auth class accessing the wrong method.
- Updated `authenticate_header` in auth classes.


## [0.3.5]

### Docs
- Updated documentation.

### Fixed
- Fixed auth class accessing an invalid variable.


## [0.3.4]

### Fixed
- Fixed documentation URLs in `pyproject.toml`.
- Fixed changelog URLs in `pyproject.toml`.


## [0.3.0]

### Added
- Initial beta release.
