from rest_framework import status
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate

from sample_project.utils import set_cookie
from drf_authentify.services import TokenService
from sample_project.serializers import (
    UserSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
)


User = get_user_model()


# Create your views here.
class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request=request, username=username, password=password)
        if user:
            # Core Usage:
            # issued_tokens = TokenService.generate_header_token(user)
            # issued_tokens = TokenService.generate_cookie_token(user)

            # optionally, you can specify a custom expiration time for token and refresh,
            # and also include context if you require like this.
            # issued_tokens = TokenService.generate_header_token(
            #     user,
            #     context={"scope": "global", "provider": "google"},
            #     access_expires_in=20,
            #     refresh_expires_in=20,
            # )

            # To generate token for cookies, simply use any of the following, same signature as used above also apply
            # to specify contexts and expiration.
            issued_tokens = TokenService.generate_cookie_token(
                user,
                context={"scope": "global", "provider": "google"},
                # access_expires_in=20,
                # refresh_expires_in=20,
            )

            data = dict()
            data["status"] = "success"
            data["message"] = "Login successful."

            # for header tokens
            data["data"] = {
                "user": UserSerializer(user).data,
                "token": issued_tokens.access_token,
                "refresh_token": issued_tokens.refresh_token,
            }
            # for headers simply return
            # return Response(data, status=status.HTTP_200_OK)

            # or set as cookie on response for cookie tokens
            response = Response(data, status=status.HTTP_200_OK)
            return set_cookie(response, token=issued_tokens.access_token)

        msg = ["Unable to log in with provided credentials."]
        raise serializers.ValidationError(msg, code="authorization")


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # revoke single token from request by:
        TokenService.revoke_token(request.auth)

        # Or revoke all expired tokens by:
        # TokenService.revoke_expired_tokens()

        # Or revoke all expired user tokens by:
        # TokenService.revoke_all_expired_user_tokens(request.user)

        # Or revoke all user tokens by:
        # TokenService.revoke_all_user_tokens(request.user)

        data = dict()
        data["status"] = "success"
        data["message"] = "Logout successful."
        data["data"] = None
        response = Response(data, status=status.HTTP_204_NO_CONTENT)
        return set_cookie(response, token="", duration=0)


class RefreshTokenView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh_token"]
        generated_token = TokenService.refresh_token(refresh_token)

        if generated_token:

            data = dict()
            data["status"] = "success"
            data["message"] = "Refresh successful."
            data["data"] = {
                "token": generated_token.access_token,
                "refresh_token": generated_token.refresh_token,
            }
            response = Response(data, status=status.HTTP_204_NO_CONTENT)
            return set_cookie(response, token="", duration=0)

        msg = ["Refresh failed."]
        raise serializers.ValidationError(msg, code="authorization")


class AccountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        # How to access your current auth token instance.
        # print(request.user)
        # print(request.auth)
        # print(request.auth.context)
        # print(request.auth.context_obj.scope)
        # print(request.auth.context_obj.provider)
        # print(request.auth.context_obj.invalid_key)

        data = dict()
        data["status"] = "success"
        data["message"] = "Account retrieved successful."
        data["data"] = UserSerializer(request.user).data
        return Response(data, status=status.HTTP_204_NO_CONTENT)
