from rest_framework import serializers
from api.models import Favorites, Card
from .card import CardSerializer

class FavoritesSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)
    card_id = serializers.PrimaryKeyRelatedField(
        queryset=Card.objects.all(),
        write_only=True,
        source='card'
    )
    
    class Meta:
        model = Favorites
        fields = ['id', 'user', 'card', 'card_id', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        favorite_count = Favorites.objects.filter(user=user).count()
        if favorite_count >= 10:
            raise serializers.ValidationError(
                "Vous ne pouvez pas avoir plus de 10 cartes favorites."
            )
        
        favorite = Favorites.objects.create(
            user=user,
            card=validated_data['card']
        )
        
        return favorite