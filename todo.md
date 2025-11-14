# TODO

- deprecate some functions
- allow use of refresh token
- hash tokens, and allow users to specify which hash to use.
- allow swappable models
- allow to add never expire tokens
- enforce single sign in
- generate token using default, so it already exists in django admin when creating for user.


settings configuration should now include.


TOKEN_TTL = # token timedelta or None
REFRESH_TOKEN_TTL =  #refresh token timedelta or none
AUTO_REFRESH = bool # allow token expiry to be extend during use.
AUTO_REFRESH_MAX_TTL =  # timedelta maximumm extension for auto refresh
AUTO_REFRESH_MIN_TTL =  # timedelta minimum time before extension can happen
TOKEN_MODEL =  # custom token model path
AUTH_COOKIE_NAMES = [] # allowed auth cookie names
AUTH_HEADER_PREFIXES = [] # allowed token header prefixes
SECURE_HASH_ALGORITHM = "" # secure hash algorithm
ENFORCE_SINGLE_LOGIN = bool # enforce single login for each uer
STRICT_CONTEXT_ACCESS = bool # raise error when undefined context params is accessed.
POST_AUTH_HANDLER
