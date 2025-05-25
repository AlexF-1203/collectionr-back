from django.contrib import admin
from .models import User, Collection, Card, Set, Favorites, CardPrice, News

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'set_name','image_url')
    search_fields = ('name', 'set_name')

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'condition', 'quantity', 'acquired_date')
    search_fields = ('user__username', 'card')

@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'release_date')
    search_fields = ('user__username', 'title', 'release_date')

@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'created_at')
    search_fields = ('user__username', 'card')

@admin.register(CardPrice)
class CardPriceAdmin(admin.ModelAdmin):
    list_display = ('card', 'avg1', 'avg7', 'avg30', 'daily_price')
    search_fields = ('card__name', 'card__set_name')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'main_image')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
