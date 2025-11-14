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
            # token = TokenService.generate_header_token(user)

            # optionally, you can specify a custom expiration time for token,
            # and also include context if you require.
            # token = TokenService.generate_header_token(
            #     user, context={"scope": "global", "provider": "google"}, expires_in=7200
            # )

            # To generate token for cookies, simply use any of the following, same signature as used above also apply
            # to specify contexts and duration.
            # token = TokenService.generate_cookie_token(user)
            generated_token = TokenService.generate_cookie_token(
                user, context={"scope": "global", "provider": "google"}
            )

            data = dict()
            data["status"] = "success"
            data["message"] = "Login successful."

            # for header tokens
            data["data"] = {
                "token": generated_token.token,
                "refresh_token": generated_token.refresh,
                "user": UserSerializer(user).data,
            }
            # return Response(data, status=status.HTTP_200_OK)

            # or set as cookie on response for cookie tokens
            response = Response(data, status=status.HTTP_200_OK)
            return set_cookie(response, token=generated_token.token)

        msg = ["Unable to log in with provided credentials."]
        raise serializers.ValidationError(msg, code="authorization")


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # revoke single token from request using:
        TokenService.revoke_token_from_request(request)

        # Or revoke all tokens for user from request using:
        # TokenService.revoke_all_tokens_for_user_from_request(request)

        # Or revoke all tokens for user using:
        # TokenService.revoke_all_user_tokens(request.user)

        # Or revoke all expired tokens, to clean up space for example using:
        # TokenService.revoke_expired_tokens()

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
                "token": generated_token.token,
                "refresh_token": generated_token.refresh,
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
