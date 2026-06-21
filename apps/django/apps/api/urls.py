from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CollectionViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'collections', CollectionViewSet, basename='collection')

urlpatterns = [
    path('health/', lambda r: __import__('django.http').http.JsonResponse({'status': 'ok'})),
    path('', include(router.urls)),
]
