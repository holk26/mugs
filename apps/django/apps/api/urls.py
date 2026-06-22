from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CollectionViewSet
from .auth_views import signup, signin
from .order_views import OrderViewSet
from .payment_views import payment_gateways, create_payment_intent, stripe_webhook, checkout_complete
from rest_framework_simplejwt.views import TokenRefreshView
from apps.printful.views import printful_webhook

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('health/', lambda r: __import__('django.http').http.JsonResponse({'status': 'ok'})),
    path('auth/signup/', signup),
    path('auth/signin/', signin),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('payments/gateways/', payment_gateways, name='payment-gateways'),
    path('payments/stripe/intent/', create_payment_intent, name='create-payment-intent'),
    path('payments/stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    path('checkout/<uuid:order_id>/complete/', checkout_complete),
    path('', include(router.urls)),
]

urlpatterns += [
    path('printful/webhook/', printful_webhook),
]
