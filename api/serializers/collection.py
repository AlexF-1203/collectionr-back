from rest_framework import serializers
from api.models import Collection
from .card import CardSerializer
from .user import UserSerializer


class CollectionSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    card_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Collection
        fields = [
            'id', 
            'user', 
            'card', 
            'card_id', 
            'quantity', 
            'condition',
            'acquired_date'
        ]
        read_only_fields = ['acquired_date']

    def create(self, validated_data):
        user = self.context['request'].user
        card_id = validated_data.pop('card_id')
        collection = Collection.objects.create(
            user=user,
            card_id=card_id,
            **validated_data
        )
        return collection