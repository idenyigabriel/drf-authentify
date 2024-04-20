from rest_framework import status
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate

from sample_project.utils import set_cookie
from drf_authentify.models import AuthToken
from sample_project.serializers import LoginSerializer, UserSerializer


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
            token = AuthToken.generate_header_token(user)

            data = dict()
            data["status"] = "success"
            data["message"] = "Login successful."
            data["data"] = UserSerializer(user).data
            response = Response(data, status=status.HTTP_200_OK)
            return set_cookie(response, token=token)

        msg = ["Unable to log in with provided credentials."]
        raise serializers.ValidationError(msg, code="authorization")


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        AuthToken.remove_token_by_request(request)

        data = dict()
        data["status"] = "success"
        data["message"] = "Logout successful."
        data["data"] = None
        response = Response(data, status=status.HTTP_204_NO_CONTENT)
        return set_cookie(response, token="", duration=0)


class LogoutAllView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        AuthToken.remove_all_tokens_by_request(request)

        data = dict()
        data["status"] = "success"
        data["message"] = "Logout all successful."
        data["data"] = None
        response = Response(data, status=status.HTTP_204_NO_CONTENT)
        return set_cookie(response, token="", duration=0)


class LogoutByUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        AuthToken.remove_all_tokens_by_user(request.user)

        data = dict()
        data["status"] = "success"
        data["message"] = "Logout by user successful."
        data["data"] = None
        response = Response(data, status=status.HTTP_204_NO_CONTENT)
        return set_cookie(response, token="", duration=0)
