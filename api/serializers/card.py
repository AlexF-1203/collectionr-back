from rest_framework import serializers
from api.models import Card, CardPrice
from .set import SetSerializer
from djmoney.contrib.django_rest_framework import MoneyField

class CardPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardPrice
        fields = ['avg1', 'avg7', 'avg30', 'daily_price']

class CardSerializer(serializers.ModelSerializer):
    price = MoneyField(max_digits=10, decimal_places=2)
    prices = CardPriceSerializer(many=True, read_only=True)
    set = SetSerializer(read_only=True)

    class Meta:
        model = Card
        fields = ['id', 'name', 'image_url', 'rarity', 'set', 'price', 'prices', 'number', 'description', 'release_date']
