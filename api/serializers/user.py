from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from api.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email", "password", "profile_picture"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},  # Rendre password facultatif ici
            "email": {"required": True}
        }

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user
