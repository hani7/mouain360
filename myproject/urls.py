from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('spancha9lo/', admin.site.urls),
    path('viewer/', include('viewer.urls')),
    path('', include('floor_plan.urls')),
    path('accounts/', include('accounts.urls')),
]

# Serve static and media files (cPanel/Passenger deployment)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

