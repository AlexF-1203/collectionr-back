from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CardViewSet, CollectionViewSet, UserViewSet, SetViewSet, FavoritesViewSet

router = DefaultRouter()
router.register(r'cards', CardViewSet)
router.register(r'collections', CollectionViewSet, basename='collection')
router.register('users', UserViewSet)
router.register('sets', SetViewSet, basename='set')
router.register('favorites', FavoritesViewSet, basename='favorites')

urlpatterns = [
    path('', include(router.urls)),
]

# urlpatterns = router.urls
