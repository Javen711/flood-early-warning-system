from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
]

# Registered separately (without the /api/ prefix) in afews/urls.py:
dashboard_urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
]
