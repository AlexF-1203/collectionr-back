from rest_framework import serializers
from api.models import Set
from .user import UserSerializer

class SetSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Set
        fields = [
            'id',
            'user', 
            'title', 
            'code', 
            'tcg', 
            'release_date', 
            'total_cards', 
            'image_url', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        set_obj = Set.objects.create(
            user=user,
            **validated_data
        )
        return set_obj