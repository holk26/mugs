from django.urls import path

urlpatterns = [
    path('health/', lambda r: __import__('django.http').http.JsonResponse({'status': 'ok'})),
]
