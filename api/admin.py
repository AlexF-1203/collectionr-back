from django.contrib import admin
from .models import User, Collection, Card, Set, Favorites, CardPrice, News, UserSet

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('name','image_url')
    search_fields = ('name', 'set__title', 'number')

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'condition', 'quantity', 'acquired_date')
    search_fields = ('user__username', 'card')

@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date')
    search_fields = ('title', 'release_date')

@admin.register(UserSet)
class UserSetAdmin(admin.ModelAdmin):
    list_display = ('user', 'set', 'card_count', 'total_cards', 'completion', 'completed')
    search_fields = ('user__username', 'set__title')
    list_filter = ('completed',)

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
