from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CardViewSet, CollectionViewSet

router = DefaultRouter()
router.register(r'cards', CardViewSet)
router.register(r'collections', CollectionViewSet, basename='collection')

urlpatterns = [
    path('', include(router.urls)),
]
