from django.db import models
from djmoney.models.fields import MoneyField


class Card(models.Model):
    """
    Modèle représentant une carte Pokémon.
    """
    RARITY_CHOICES = [
        ('COMMON', 'Common'),
        ('UNCOMMON', 'Uncommon'),
        ('RARE', 'Rare'),
        ('HOLORARE', 'Holo Rare'),
        ('ULTRARARE', 'Ultra Rare'),
        ('SECRETRARE', 'Secret Rare'),
    ]

    name = models.CharField(max_length=100)
    set_name = models.CharField(max_length=100)
    number = models.CharField(max_length=20)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES)
    image_url = models.URLField()
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    description = models.TextField(blank=True)
    release_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['set_name', 'number']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.set_name} #{self.number})"


class CardPrice(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='prices')
    avg1 = models.DecimalField(max_digits=10, decimal_places=2)
    avg7 = models.DecimalField(max_digits=10, decimal_places=2)
    avg30 = models.DecimalField(max_digits=10, decimal_places=2)
    daily_price = models.JSONField(default=dict)
    
    def calculate_daily_price(self):
        daily_prices = {}
        avg1, avg7, avg30 = float(self.avg1), float(self.avg7), float(self.avg30)
        
        # Analyser les tendances
        trend1 = avg7 - avg1  # Tendance entre J1 et J7
        trend2 = avg30 - avg7  # Tendance entre J7 et J30
        
        # Déterminer si nous devons modéliser des fluctuations
        should_fluctuate = False
        
        # Si la tendance globale est à la hausse mais avec une intensité différente
        # ou si les tendances sont opposées, ajoutons des fluctuations
        if (trend1 > 0 and trend2 > 0 and abs(trend1/6 - trend2/23) > 0.05) or (trend1 * trend2 < 0):
            should_fluctuate = True
        
        # Créer des points de contrôle supplémentaires
        control_points = []
        control_points.append((1, avg1))
        control_points.append((7, avg7))
        control_points.append((30, avg30))
        
        # Ajouter des points de contrôle intermédiaires pour les fluctuations si nécessaire
        if should_fluctuate:
            if trend1 > 0 and trend2 < 0:  # Hausse puis baisse
                # Point haut entre J7 et J15
                peak_day = 12
                peak_value = avg7 + (avg7 - avg1) * 0.15  # Un peu plus haut que avg7
                control_points.append((peak_day, peak_value))
            elif trend1 < 0 and trend2 > 0:  # Baisse puis hausse
                # Point bas entre J7 et J15
                trough_day = 12
                trough_value = avg7 - (avg1 - avg7) * 0.15  # Un peu plus bas que avg7
                control_points.append((trough_day, trough_value))
            elif abs(trend1) > abs(trend2) and trend1 * trend2 > 0:  # Même direction mais ralentissement
                # Point d'inflexion
                mid_day = 15
                mid_value = avg7 + (trend2 / 23) * 8  # Valeur attendue au jour 15 selon tendance 2
                control_points.append((mid_day, mid_value))
        
        # Trier les points de contrôle par jour
        control_points.sort(key=lambda x: x[0])
        
        # Interpolation par spline naturelle entre tous les points de contrôle
        from scipy.interpolate import PchipInterpolator
        
        days = [point[0] for point in control_points]
        values = [point[1] for point in control_points]
        
        # Utiliser PchipInterpolator qui préserve la monotonie locale des données
        # (moins d'oscillations non naturelles que CubicSpline)
        interpolator = PchipInterpolator(days, values)
        
        # Générer les prix pour tous les jours
        for day in range(1, 31):
            price = float(interpolator(day))
            daily_prices[f"day_{day}"] = round(price, 2)
        
        # S'assurer que les points d'ancrage sont respectés exactement
        daily_prices["day_1"] = round(avg1, 2)
        daily_prices["day_7"] = round(avg7, 2)
        daily_prices["day_30"] = round(avg30, 2)
        
        self.daily_price = daily_prices
    
    def save(self, *args, **kwargs):
        self.calculate_daily_price()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['card']