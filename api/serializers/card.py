from rest_framework import serializers
from api.models import Card
from djmoney.contrib.django_rest_framework import MoneyField


class CardSerializer(serializers.ModelSerializer):
    price = MoneyField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = Card
        fields = '__all__'