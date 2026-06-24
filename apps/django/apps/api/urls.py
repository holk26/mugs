from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CollectionViewSet
from .auth_views import signup, signin
from .order_views import OrderViewSet
from .payment_views import payment_gateways, create_payment_intent, stripe_webhook
from rest_framework_simplejwt.views import TokenRefreshView
from apps.printful.views import printful_webhook
from .admin_views import (
    AdminUserViewSet,
    AdminProductViewSet,
    AdminProductVariantViewSet,
    AdminProductMediaViewSet,
    AdminOrderViewSet,
    AdminPrintfulViewSet,
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'orders', OrderViewSet, basename='order')

admin_router = DefaultRouter()
admin_router.register(r'users', AdminUserViewSet, basename='admin-user')
admin_router.register(r'products', AdminProductViewSet, basename='admin-product')
admin_router.register(r'orders', AdminOrderViewSet, basename='admin-order')

urlpatterns = [
    path('health/', lambda r: __import__('django.http').http.JsonResponse({'status': 'ok'})),
    path('auth/signup/', signup),
    path('auth/signin/', signin),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('payments/gateways/', payment_gateways, name='payment-gateways'),
    path('payments/stripe/intent/', create_payment_intent, name='create-payment-intent'),
    path('payments/stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    path('', include(router.urls)),
]

urlpatterns += [
    path('printful/webhook/', printful_webhook),
]

urlpatterns += [
    path('admin/', include([
        path('', include(admin_router.urls)),
        path('products/<uuid:product_id>/variants/', include([
            path('', AdminProductVariantViewSet.as_view({'get': 'list', 'post': 'create'})),
            path('<uuid:id>/', AdminProductVariantViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
        ])),
        path('products/<uuid:product_id>/media/', include([
            path('', AdminProductMediaViewSet.as_view({'get': 'list', 'post': 'create'})),
            path('<uuid:id>/', AdminProductMediaViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
        ])),
        path('printful/', include([
            path('sync/', AdminPrintfulViewSet.as_view({'post': 'sync'})),
            path('logs/', AdminPrintfulViewSet.as_view({'get': 'logs'})),
            path('webhooks/', AdminPrintfulViewSet.as_view({'get': 'webhooks'})),
        ])),
    ])),
]
