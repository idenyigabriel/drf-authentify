# 🔒 DRF Authentify

**Reimagined Authentication for Django Rest Framework**

A powerful, modern, and highly flexible token-based authentication library for Django Rest Framework (DRF), completely re-engineered for simplicity, security, and modularity.

---

## ✨ Why drf-authentify?

`drf-authentify` provides a superior replacement for DRF's default token system with features tailored for modern web and mobile applications:

### 🔑 Multiple Active Tokens
Unlike traditional systems that force single-device sessions, `drf-authentify` allows users to maintain **multiple active tokens simultaneously**. This enables seamless authentication across:
- 📱 Mobile apps
- 🌐 Web browsers  
- 💻 Desktop clients

**No more forced logouts** when users switch devices!

### 🛡️ Contextual Security
Every token stores rich, session-specific metadata in a `context` JSONField:

```python
{
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "device_id": "iPhone-12-XYZ",
    "beta_access": true
}
```

This enables:
- **Granular authorization** based on device or location
- **Session monitoring** and analytics
- **Targeted token revocation** (e.g., revoke only mobile sessions)
- **Feature flags** per session

### 🔄 Auto Token Refresh
Balance security and user experience with **automatic token renewal**:

- Tokens refresh seamlessly during active use
- No forced re-login for active users
- Configurable refresh intervals and maximum lifespans
- Security enforced through `AUTO_REFRESH_MAX_TTL`

Users stay authenticated while you maintain strict security policies.

### 🧱 Modular Architecture
Clean separation of concerns makes the codebase:
- **Easy to audit** - Clear module boundaries
- **Simple to debug** - Isolated functionality
- **Highly extensible** - Swap or customize any component

---

## 📦 Installation

### Requirements
- Python ≥ 3.8
- Django ≥ 3.2
- Django REST Framework ≥ 3.0

### Install via pip

```bash
pip install drf-authentify
```

---

## ⚙️ Quick Setup

### 1. Add to Installed Apps

```python
# settings.py

INSTALLED_APPS = [
    # ... other apps
    'drf_authentify',
]
```

### 2. Configure DRF Authentication

```python
# settings.py

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'drf_authentify.auth.AuthorizationHeaderAuthentication',
        'drf_authentify.auth.CookieAuthentication',
    ],
}
```

### 3. Run Migrations

```bash
python manage.py migrate
```

This creates the `AuthToken` model with fields for access tokens, refresh tokens, context, and expiration tracking.

---

## 🛠️ Configuration

Customize behavior by adding a `DRF_AUTHENTIFY` dictionary to your `settings.py`. All time values use `datetime.timedelta` for clarity.

### Basic Configuration

```python
# settings.py
from datetime import timedelta

# defaults
DRF_AUTHENTIFY = {
    "TOKEN_TTL": timedelta(hours=12),
    "REFRESH_TOKEN_TTL": timedelta(days=1),
    "AUTO_REFRESH": False,
    "AUTO_REFRESH_MAX_TTL": timedelta(days=30),
    "AUTO_REFRESH_INTERVAL": timedelta(hours=1),
    "TOKEN_MODEL": "drf_authentify.AuthToken",
    "AUTH_COOKIE_NAMES": ["token"],
    "AUTH_HEADER_PREFIXES": ["Bearer", "Token"],
    "SECURE_HASH_ALGORITHM": "sha256",
    "ENFORCE_SINGLE_LOGIN": True,
    "STRICT_CONTEXT_ACCESS": False,
    "ENABLE_AUTH_RESTRICTION": True,
    "KEEP_EXPIRED_TOKENS": False,
    "POST_AUTH_HANDLER": None,
}
```

### All Available Settings and Descriptions

| Setting | Type | Description |
|---------|------|-------------|
| `TOKEN_MODEL` | `str` | Path to custom token model (default: built-in `AuthToken`) |
| `TOKEN_TTL` | `timedelta` | Access token lifespan (e.g., 12 hours) |
| `REFRESH_TOKEN_TTL` | `timedelta` | Refresh token lifespan. Must be > `TOKEN_TTL` |
| `AUTO_REFRESH` | `bool` | Enable automatic token renewal |
| `AUTO_REFRESH_INTERVAL` | `timedelta` | Minimum time between auto refreshes (prevents excessive DB updates) |
| `AUTO_REFRESH_MAX_TTL` | `timedelta` | Maximum token age before forced expiry |
| `AUTH_HEADER_PREFIXES` | `list[str]` | Valid Authorization header prefixes |
| `AUTH_COOKIE_NAMES` | `list[str]` | Cookie keys to check for tokens |
| `SECURE_HASH_ALGORITHM` | `str` | Hashing algorithm for token storage (default: `"sha256"`) |
| `ENABLE_AUTH_RESTRICTION` | `bool` | If `True`, cookie tokens can't be used in headers (and vice versa) |
| `ENFORCE_SINGLE_LOGIN` | `bool` | If `True`, new tokens revoke all previous user tokens |
| `KEEP_EXPIRED_TOKENS` | `bool` | Keep revoked tokens for audit logging (requires `ENFORCE_SINGLE_LOGIN`) |
| `STRICT_CONTEXT_ACCESS` | `bool` | If `True`, accessing undefined context keys raises `KeyError` |
| `POST_AUTH_HANDLER` | `str` | Path to custom function called after successful authentication |

### Settings Validation

The library automatically validates your configuration on startup:

- ✅ **Type checking** - Ensures values match expected types
- ✅ **Algorithm verification** - Confirms hash algorithm exists in `hashlib`
- ✅ **Logical integrity** - Validates relationships (e.g., `REFRESH_TOKEN_TTL > TOKEN_TTL`)

---

## 📖 Usage Guide

### Creating Tokens

Use `TokenService` to generate tokens programmatically *(where context and expires_in are optional)*:

```python
from drf_authentify.services import TokenService

# Generate a header token
token_set = TokenService.generate_header_token(
    user=request.user,
    context={
        "device": "mobile",
        "app_version": "2.1.0",
        "ip_address": request.META.get('REMOTE_ADDR')
    },
    expires_in=3600  # Override default TTL (in seconds)
)

# OR 

# Generate a cookie token
token_set = TokenService.generate_cookie_token(
    user=request.user,
    context={
        "device": "mobile",
        "app_version": "2.1.0",
        "ip_address": request.META.get('REMOTE_ADDR')
    },
    expires_in=3600  # Override default TTL (in seconds)
)

# Return to client
response_data = {
    'access_token': token_set.token,      # Raw token string
    'refresh_token': token_set.refresh,   # Raw refresh token
}
```

The `generate_header_token` method returns a `GeneratedToken` object with:

| Field | Type | Description |
|-------|------|-------------|
| `token` | `str` | Raw access token (send to client) |
| `refresh` | `str` | Raw refresh token (send to client) |
| `instance` | `AuthToken` | Database model instance |

### Refreshing Tokens

Implement a token refresh endpoint:

```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from drf_authentify.services import TokenService


class TokenRefreshView(APIView):
    authentication_classes = [AllowAny]  # No auth required for refresh
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'error': 'refresh_token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Attempt to refresh the token
        # optionally provide expires_in to override default TOKEN_TTL here.
        new_token_set = TokenService.refresh_token(refresh_token,  expires_in: int = None)
        
        if new_token_set:
            return Response({
                'access_token': new_token_set.token,
                'refresh_token': new_token_set.refresh,
            })
        else:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
```

**Security Note:** The old token is automatically revoked when a refresh succeeds, preventing token reuse attacks.

### Accessing Token Context

Access session metadata in your views:

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    # Access context data
    device = request.auth.context_obj.device
    app_version = request.auth.context_obj.app_version
    
    # Check token expiration
    if request.auth.is_expired:
        return Response({'error': 'Token expired'}, status=401)
    
    return Response({
        'message': f'Authenticated from {device}',
        'version': app_version
    })
```

**Note:** If `STRICT_CONTEXT_ACCESS=False`, accessing undefined keys returns `None` instead of raising `KeyError`.

### Revoking Tokens

```python
# Revoke all tokens for a user
from drf_authentify.services import TokenService

# revoke single token
TokenService.revoke_token(token_instance)

# revoke all user tokens
TokenService.revoke_all_user_tokens(user_instance)

# revoke all expired user tokens
TokenService.revoke_all_expired_user_tokens(user_instance)


# revoke all expired tokens
TokenService.revoke_expired_tokens()
```

**Note:** token instance is accessible via request.auth

---

## 🏗️ Architecture Overview

### Models (`drf_authentify.models`)

**`AuthToken`** - Core database model (inherits from `AbstractAuthToken`)

```python
class AuthToken(AbstractAuthToken):
    user = ForeignKey(User)           # Associated user
    token = CharField()               # Hashed access token
    refresh_token = CharField()       # Hashed refresh token
    context = JSONField()             # Session metadata
    created_at = DateTimeField()      # Token creation time
    expires_at = DateTimeField()      # Token expiration time
    refresh_expires_at = DateTimeField()  # Refresh token expiration
```

**Customizing Token Models:**

```python
# myapp/models.py
from drf_authentify.models import AbstractAuthToken

class CustomAuthToken(AbstractAuthToken):
    last_ip = GenericIPAddressField()
    two_factor_verified = BooleanField(default=False)
    
# settings.py
DRF_AUTHENTIFY = {
    'TOKEN_MODEL': 'myapp.CustomAuthToken',
}
```

### Authentication Classes (`drf_authentify.auth`)

**`AuthorizationHeaderAuthentication`** - Checks `Authorization` header

```python
# Validates: Authorization: Bearer <token>
# Checks prefixes: AUTH_HEADER_PREFIXES setting
```

**`CookieAuthentication`** - Checks request cookies

```python
# Checks cookie names: AUTH_COOKIE_NAMES setting
```

Both classes handle:
- Token lookup and validation
- Expiration checking
- Auto-refresh (if enabled)
- Context restrictions (if enabled)

### Services (`drf_authentify.services`)

**`TokenService`** - High-level business logic API

| Method | Description |
|--------|-------------|
| `generate_header_token(user, context, expires_in)` | Create token for header auth |
| `generate_cookie_token(user, context, expires_in)` | Create token for cookie auth |
| `refresh_token(refresh_token_str)` | Refresh an existing token |
| `verify_token(token_str, auth_type)` | Verify token |
| `revoke_token(token_str)` | Manually revoke a token |
| `revoke_all_user_tokens(user)` | Manually revoke all user token |
| `revoke_all_expired_user_tokens(user)` | Manually revoke all expired user tokens |
| `revoke_expired_tokens(token_str)` | Manually revoke all expired tokens |

### Security (`drf_authentify.utils`)

- **`generate_token_string_hash()`** - Creates cryptographically secure tokens using `secrets.token_urlsafe`
- **Zero raw storage** - Only hashed tokens stored in database
- **Configurable algorithms** - Use any `hashlib` algorithm

**Why hashing matters:** If your database is compromised, attackers cannot use stored hashes to authenticate.

### Validation (`drf_authentify.validators`)

**`validate_dict`** - Ensures `context` field only accepts valid dictionaries, preventing serialization errors.

---

## 🔒 Security Best Practices

### 1. Token Storage (Client-Side)

**Mobile Apps:**
```javascript
// Use secure storage
import SecureStorage from 'react-native-secure-storage';

await SecureStorage.setItem('access_token', token);
```

**Web Apps:**
```javascript
// Use httpOnly cookies (set server-side)
// Never store tokens in localStorage!
```

### 2. HTTPS Only

```python
# settings.py
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
```

### 3. Token Extension

Enable auto-refresh with reasonable limits:

```python
DRF_AUTHENTIFY = {
    'AUTO_REFRESH': True,
    'AUTO_REFRESH_INTERVAL': timedelta(hours=1),  # Don't refresh too often
    'AUTO_REFRESH_MAX_TTL': timedelta(days=7),    # Force re-login after 7 days
}
```

### 4. Context-Based Validation

```python
# In a view or custom permission
# ideally, you can also use the POST_AUTH_HANDLER, where user and token are provided to perform this glovally
def check_device_binding(request):
    stored_device = request.auth.context_obj.device_id
    current_device = request.META.get('HTTP_X_DEVICE_ID')
    
    if stored_device != current_device:
        raise PermissionDenied("Device mismatch detected")
```

### 5. Monitor and Audit

Keep expired tokens for security audits:

```python
DRF_AUTHENTIFY = {
    'ENFORCE_SINGLE_LOGIN': False,
    'KEEP_EXPIRED_TOKENS': True,  # Retain for forensics
}
```

---

## 🎯 Common Use Cases

### Multi-Device Support

```python
# User can be logged in on multiple devices simultaneously
phone_token = TokenService.generate_header_token(
    user=user,
    context={"device": "mobile", "device_id": "abc123"}
)

laptop_token = TokenService.generate_header_token(
    user=user,
    context={"device": "laptop", "device_id": "xyz789"}
)
```

### Feature Flags per Session

```python
# Enable beta features for specific tokens
beta_token = TokenService.generate_header_token(
    user=user,
    context={"beta_access": True, "features": ["new_ui", "advanced_search"]}
)

# In view:
if request.auth.context_obj.beta_access:
    return beta_feature_response()
```

### Geographic Restrictions

```python
# Store location on token creation
token = TokenService.generate_header_token(
    user=user,
    context={"country": "US", "ip": request.META['REMOTE_ADDR']}
)

# Validate in view:
if request.auth.context_obj.country != "US":
    raise PermissionDenied("Service not available in your region")
```

### Single Login Enforcement

```python
# Force single active session (revoke old tokens on new login)
DRF_AUTHENTIFY = {
    'ENFORCE_SINGLE_LOGIN': True,
}
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- ✅ Tests pass
- ✅ Code follows PEP 8
- ✅ Documentation is updated

---

## 📝 License

This project is licensed under the **BSD-3-Clause License**. See the [LICENSE](LICENSE) file for details.

---

## 🔗 Resources

- **Documentation:** [Coming Soon]
- **Issue Tracker:** [GitHub Issues](https://github.com/yourusername/drf-authentify/issues)
- **PyPI:** [https://pypi.org/project/drf-authentify/](https://pypi.org/project/drf-authentify/)

---

## ⭐ Show Your Support

If you find this library helpful, please consider giving it a star on GitHub!

---

**Built with ❤️ for the Django community**