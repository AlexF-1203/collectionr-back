from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Card, Collection

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

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
