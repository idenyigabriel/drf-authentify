from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("username", "email")
