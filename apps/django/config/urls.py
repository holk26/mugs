from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.api.urls')),
]

# Serve user-uploaded media files in both debug and production.
# django.conf.urls.static.static() no-ops when DEBUG=False, so we wire the
# serve view explicitly to keep /media/ reachable behind Traefik.
if settings.MEDIA_URL and settings.MEDIA_ROOT:
    urlpatterns += [
        re_path(
            r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
