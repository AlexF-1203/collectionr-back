from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CardViewSet, CollectionViewSet, UserViewSet, SetViewSet, FavoritesViewSet, NewsViewSet
from .views.user import LogoutView

router = DefaultRouter()
router.register(r'cards', CardViewSet)
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'users', UserViewSet)
router.register(r'sets', SetViewSet, basename='set')
router.register(r'favorites', FavoritesViewSet, basename='favorites')
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = [
    path('', include(router.urls)),
    path('user/profile/', UserViewSet.as_view({'get': 'profile'}), name='user-profile'),
    path('user/update/', UserViewSet.as_view({'patch': 'update_profile'}), name='user-profile-update'),
    path('user/profile/data/', UserViewSet.as_view({'get': 'profile_data'}), name='user-profile-data'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
