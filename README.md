# 🔒 DRF Authentify

[![Build Status](https://github.com/idenyigabriel/drf-authentify/actions/workflows/test.yml/badge.svg)](https://github.com/idenyigabriel/drf-authentify/actions/workflows/test.yml)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

**Modern token authentication for Django Rest Framework with multi-device support, auto-refresh, and session context.**

---

## Why Choose DRF Authentify?

DRF Authentify reimagines token authentication for modern applications. Unlike DRF's default token system, it provides:

- **Multi-device sessions** - Users stay logged in across mobile, web, and desktop simultaneously
- **Session context** - Store device info, IP addresses, and custom metadata with each token
- **Auto-refresh** - Tokens renew automatically during active use
- **Flexible security** - Choose between single-login enforcement or multiple active sessions
- **Production-ready** - Secure token hashing, expiration management, and audit trails

---

## Installation

```bash
pip install drf-authentify
```

**Requirements:** Python ≥ 3.9, Django ≥ 3.2, Django REST Framework ≥ 3.0

---

## Quick Start

### 1. Add to Your Project

```python
# settings.py

INSTALLED_APPS = [
    # ... your apps
    'drf_authentify',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'drf_authentify.auth.AuthorizationHeaderAuthentication',
        'drf_authentify.auth.CookieAuthentication',
    ],
}
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Create Your First Token

```python
from drf_authentify.services import TokenService

# In your login view
token_set = TokenService.generate_header_token(
    user=request.user,
    context={
        "device": "mobile",
        "ip_address": request.META.get('REMOTE_ADDR')
    }
)

# Return to client
return Response({
    'access_token': token_set.access_token,
    'refresh_token': token_set.refresh_token,
})
```

Your API is now protected! Clients authenticate by sending:

```
Authorization: Bearer <access_token>
```

---

## Core Concepts

### Multi-Device Authentication

Users can maintain multiple active sessions across different devices. Each token stores its own context:

```python
# Mobile login
mobile_token = TokenService.generate_header_token(
    user=user,
    context={"device": "iPhone", "app_version": "2.1"}
)

# Web login (doesn't invalidate mobile token)
web_token = TokenService.generate_header_token(
    user=user,
    context={"device": "Chrome", "browser_version": "120"}
)
```

To enforce single-device login instead:

```python
# settings.py
DRF_AUTHENTIFY = {
    'ENFORCE_SINGLE_LOGIN': True,
}
```

### Session Context

Store custom metadata with each token for authorization decisions:

```python
token_set = TokenService.generate_header_token(
    user=user,
    context={
        "device_id": "abc-123",
        "location": "US",
        "beta_features": True,
        "subscription_tier": "premium"
    }
)

# Access in your views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def premium_feature(request):
    if not request.auth.context_obj.beta_features:
        return Response({'error': 'Beta access required'}, status=403)
    
    # request.auth is the token instance
    device = request.auth.context_obj.device_id
    return Response({'message': f'Hello from {device}!'})
```

### Token Refresh

Implement a refresh endpoint to issue new access tokens without re-authentication:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_authentify.services import TokenService

class TokenRefreshView(APIView):
    permission_classes = []  # No auth required
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({'error': 'refresh_token required'}, status=400)
        
        new_token_set = TokenService.refresh_token(refresh_token)
        
        if new_token_set:
            return Response({
                'access_token': new_token_set.access_token,
                'refresh_token': new_token_set.refresh_token,
            })
        
        return Response({'error': 'Invalid refresh token'}, status=401)
```

**Security:** Old tokens are automatically revoked when refreshed.

### Auto-Refresh

Enable automatic token renewal for active users:

```python
# settings.py
from datetime import timedelta

DRF_AUTHENTIFY = {
    'AUTO_REFRESH': True,
    'AUTO_REFRESH_INTERVAL': timedelta(hours=1),     # Minimum time between refreshes
    'AUTO_REFRESH_MAX_TTL': timedelta(days=7),       # Force re-login after 7 days
    'TOKEN_TTL': timedelta(hours=12),
    'REFRESH_TOKEN_TTL': timedelta(days=7),
}
```

With this enabled, tokens automatically renew during API requests, keeping active users logged in.

---

## Configuration

Configure behavior by adding `DRF_AUTHENTIFY` to your `settings.py`:

```python
from datetime import timedelta

DRF_AUTHENTIFY = {
    # Token Lifespans
    'TOKEN_TTL': timedelta(hours=24),              # Access token duration
    'REFRESH_TOKEN_TTL': timedelta(days=7),        # Refresh token duration
    
    # Auto-Refresh Settings
    'AUTO_REFRESH': False,                         # Enable automatic renewal
    'AUTO_REFRESH_INTERVAL': timedelta(hours=1),   # Min time between refreshes
    'AUTO_REFRESH_MAX_TTL': timedelta(days=7),     # Max token age before forced re-login
    
    # Authentication Behavior
    'ENFORCE_SINGLE_LOGIN': False,                 # Revoke old tokens on new login
    'ENABLE_AUTH_RESTRICTION': True,               # Prevent cookie tokens in headers (and vice versa)
    
    # Security
    'SECURE_HASH_ALGORITHM': 'sha256',             # Token hashing algorithm
    'AUTH_HEADER_PREFIXES': ['Bearer', 'Token'],   # Allowed header prefixes
    'AUTH_COOKIE_NAMES': ['token'],                # Cookie names to check
    
    # Audit & Cleanup
    'KEEP_EXPIRED_TOKENS': False,                  # Retain expired tokens for audit logs
    
    # Advanced
    'STRICT_CONTEXT_ACCESS': False,                # Raise errors for undefined context keys
    'TOKEN_MODEL': 'drf_authentify.AuthToken',     # Custom token model path
    'POST_AUTH_HANDLER': None,                     # Custom post-authentication function
    'POST_AUTO_REFRESH_HANDLER': None,             # Custom post-refresh function
}
```

### Key Settings Explained

| Setting | Description |
|---------|-------------|
| `TOKEN_TTL` | How long access tokens remain valid. Set to `None` for no expiration. |
| `REFRESH_TOKEN_TTL` | How long refresh tokens remain valid. Must be greater than `TOKEN_TTL`. Set to `None` to disable refresh tokens. |
| `AUTO_REFRESH` | When `True`, tokens automatically renew during API requests. Requires `AUTO_REFRESH_INTERVAL` and `AUTO_REFRESH_MAX_TTL`. |
| `AUTO_REFRESH_MAX_TTL` | Maximum token age before requiring full re-authentication, even with auto-refresh enabled. |
| `ENFORCE_SINGLE_LOGIN` | When `True`, creating a new token revokes all existing user tokens. |
| `ENABLE_AUTH_RESTRICTION` | When `True`, tokens created for cookies can't be used in headers and vice versa. |
| `KEEP_EXPIRED_TOKENS` | When `True`, expired tokens remain in the database for audit purposes (useful with `ENFORCE_SINGLE_LOGIN`). |

---

## Common Tasks

### Creating Tokens

**For header-based authentication (mobile/API clients):**

```python
from drf_authentify.services import TokenService

token_set = TokenService.generate_header_token(
    user=user,
    context={"device": "mobile"},
    access_expires_in=3600,   # Optional: override TOKEN_TTL (in seconds)
    refresh_expires_in=7200   # Optional: override REFRESH_TOKEN_TTL (in seconds)
)
```

**For cookie-based authentication (web browsers):**

```python
token_set = TokenService.generate_cookie_token(
    user=user,
    context={"browser": "Chrome"},
    access_expires_in=3600,   # Optional: override TOKEN_TTL (in seconds)
    refresh_expires_in=7200   # Optional: override REFRESH_TOKEN_TTL (in seconds)
)

# Set as httpOnly cookie in response
response.set_cookie(
    'token',
    token_set.access_token,
    httponly=True,
    secure=True,
    samesite='Strict'
)
```

### Accessing Token Information

In your views, `request.auth` provides the token instance:

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    # Access context data
    device = request.auth.context_obj.device
    
    # Check expiration
    if request.auth.is_expired:
        return Response({'error': 'Token expired'}, status=401)
    
    # Access token metadata
    created = request.auth.created_at
    expires = request.auth.expires_at
    
    return Response({
        'user': request.user.username,
        'device': device,
        'token_created': created
    })
```

### Revoking Tokens

```python
from drf_authentify.services import TokenService

# Revoke a specific token
TokenService.revoke_token(request.auth)

# Revoke all tokens for a user (force logout everywhere)
TokenService.revoke_all_user_tokens(user)

# Revoke all expired tokens for a user
TokenService.revoke_all_expired_user_tokens(user)

# Clean up all expired tokens (run as scheduled task)
TokenService.revoke_expired_tokens()
```

### Verifying Tokens Manually

```python
from drf_authentify.services import TokenService

token_instance = TokenService.verify_token(
    token_str="abc123...",
    auth_type="header"  # or "cookie"
)

if token_instance:
    user = token_instance.user
    # Token is valid
else:
    # Invalid or expired token
    pass
```

---

## Advanced Usage

### Custom Token Models

Extend the base token model with additional fields:

```python
# myapp/models.py
from drf_authentify.models import AbstractAuthToken

class CustomAuthToken(AbstractAuthToken):
    last_used_ip = models.GenericIPAddressField(null=True)
    two_factor_verified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'custom_auth_tokens'
```

Then configure it:

```python
# settings.py
DRF_AUTHENTIFY = {
    'TOKEN_MODEL': 'myapp.CustomAuthToken',
}
```

### Post-Authentication Hooks

Execute custom logic after authentication or token refresh:

```python
# myapp/handlers.py
def my_post_auth_handler(user, token, token_str):
    """Called after successful authentication"""
    # Update last login IP
    token.last_used_ip = token.context.get('ip_address')
    token.save()
    
    # Must return (user, token) tuple
    return user, token

def my_post_refresh_handler(user, token, token_str):
    """Called after successful token refresh"""
    # Log refresh event
    logger.info(f"Token refreshed for {user.username}")
    return user, token
```

Configure in settings:

```python
# settings.py
DRF_AUTHENTIFY = {
    'POST_AUTH_HANDLER': 'myapp.handlers.my_post_auth_handler',
    'POST_AUTO_REFRESH_HANDLER': 'myapp.handlers.my_post_refresh_handler',
}
```

Both handlers receive:
- `user` - The authenticated user instance
- `token` - The token instance (AuthToken or your custom model)
- `token_str` - The raw token string

Both must return a tuple: `(user, token)`

### Context-Based Authorization

Implement custom permissions based on token context:

```python
from rest_framework.permissions import BasePermission

class RequireMobileDevice(BasePermission):
    def has_permission(self, request, view):
        if not request.auth:
            return False
        return request.auth.context_obj.device == "mobile"

# Use in views
@api_view(['GET'])
@permission_classes([IsAuthenticated, RequireMobileDevice])
def mobile_only_feature(request):
    return Response({'message': 'Mobile exclusive content'})
```

---

## Security Best Practices

### 1. Always Use HTTPS in Production

```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 2. Store Tokens Securely on Clients

**Mobile apps:** Use secure storage (Keychain, Keystore)
**Web apps:** Use httpOnly cookies, never localStorage

```javascript
// ❌ DON'T: Store in localStorage
localStorage.setItem('token', token);

// ✅ DO: Let server set httpOnly cookie
// Or use secure storage in mobile apps
```

### 3. Implement Rate Limiting

Protect authentication endpoints:

```python
# Using django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Your login logic
    pass
```

### 4. Monitor Suspicious Activity

Use context data to detect anomalies:

```python
def check_location_change(request):
    """Alert if token used from different location"""
    stored_ip = request.auth.context_obj.ip_address
    current_ip = request.META.get('REMOTE_ADDR')
    
    if stored_ip != current_ip:
        # Log suspicious activity
        logger.warning(f"IP mismatch for {request.user}: {stored_ip} -> {current_ip}")
```

### 5. Set Appropriate Token Lifespans

Balance security and user experience:

```python
DRF_AUTHENTIFY = {
    # Short-lived access tokens
    'TOKEN_TTL': timedelta(hours=1),
    
    # Longer refresh tokens
    'REFRESH_TOKEN_TTL': timedelta(days=7),
    
    # Force full re-auth weekly
    'AUTO_REFRESH_MAX_TTL': timedelta(days=7),
}
```

---

## Troubleshooting

### Tokens Not Working After Migration

Run migrations and restart your server:

```bash
python manage.py migrate drf_authentify
python manage.py runserver
```

### "Invalid Token" Errors

Check that:
1. The token exists and hasn't expired
2. The correct authentication class is configured
3. The token hash algorithm matches your settings
4. The token is sent with the correct prefix (`Bearer` or `Token`)

### Auto-Refresh Not Triggering

Ensure all three settings are configured:

```python
DRF_AUTHENTIFY = {
    'AUTO_REFRESH': True,
    'AUTO_REFRESH_INTERVAL': timedelta(hours=1),
    'AUTO_REFRESH_MAX_TTL': timedelta(days=7),
}
```

### Context Data Not Available

Make sure you're accessing `request.auth.context_obj`, not `request.auth.context`:

```python
# ✅ Correct
device = request.auth.context_obj.device

# ❌ Wrong
device = request.auth.context.device
```

---

## Example: Complete Login/Logout Flow

```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from drf_authentify.services import TokenService

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)
        
        # Generate token with context
        token_set = TokenService.generate_header_token(
            user=user,
            context={
                'device': request.data.get('device', 'unknown'),
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )
        
        return Response({
            'access_token': token_set.access_token,
            'refresh_token': token_set.refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Revoke current token
        TokenService.revoke_token(request.auth)
        return Response({'message': 'Logged out successfully'})

class LogoutAllDevicesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Revoke all user tokens
        TokenService.revoke_all_user_tokens(request.user)
        return Response({'message': 'Logged out from all devices'})
```

---

## Contributing

We welcome contributions! To get started:

1. Fork the repository on GitHub
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

Please ensure your code follows PEP 8 and includes appropriate tests.

---

## License

Licensed under the **BSD-3-Clause License**. See [LICENSE](LICENSE) for details.

---

## Resources

- **GitHub:** [github.com/idenyigabriel/drf-authentify](https://github.com/idenyigabriel/drf-authentify)
- **PyPI:** [pypi.org/project/drf-authentify](https://pypi.org/project/drf-authentify/)
- **Issues:** [GitHub Issues](https://github.com/idenyigabriel/drf-authentify/issues)

---

**Built with ❤️ for the Django community**