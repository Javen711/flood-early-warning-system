from django.contrib import admin
from django.urls import include, path

from core.urls import dashboard_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),

    path('', include(dashboard_urlpatterns)),
    path('accounts/', include('accounts.urls')),
    path('zones/', include('zones.urls')),
    path('residents/', include('residents.urls')),
    path('monitoring/', include('monitoring.urls')),
]
