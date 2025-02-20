from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Card, Collection
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email", "password"]
        extra_kwargs = {
            "password": {"write_only": True, "required": True},
            "email": {"required": True}
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'

class CollectionSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    card_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'user', 'card', 'card_id', 'quantity', 'condition',
                 'is_foil', 'acquired_date', 'notes']
        read_only_fields = ['acquired_date']

    def create(self, validated_data):
        # Get the current user from the context
        user = self.context['request'].user
        # Extract card_id and remove it from validated_data
        card_id = validated_data.pop('card_id')
        # Create the collection entry
        collection = Collection.objects.create(
            user=user,
            card_id=card_id,
            **validated_data
        )
        return collection

# ceci est un commentaire
