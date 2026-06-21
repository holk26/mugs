from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CollectionViewSet
from .auth_views import signup, signin
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'collections', CollectionViewSet, basename='collection')

urlpatterns = [
    path('health/', lambda r: __import__('django.http').http.JsonResponse({'status': 'ok'})),
    path('auth/signup/', signup),
    path('auth/signin/', signin),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('', include(router.urls)),
]
