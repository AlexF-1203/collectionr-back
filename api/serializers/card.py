from rest_framework import serializers
from api.models import Card, CardPrice
from djmoney.contrib.django_rest_framework import MoneyField


class CardPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardPrice
        fields = ['avg1', 'avg7', 'avg30', 'daily_price']


class CardSerializer(serializers.ModelSerializer):
    price = MoneyField(max_digits=10, decimal_places=2)
    prices = CardPriceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Card
        fields = '__all__'