from django.urls import path

from . import views

urlpatterns = [
    path('zones/', views.ZoneListView.as_view(), name='api-zones'),
    path('auth/register/', views.RegisterView.as_view(), name='api-register'),
    path('auth/login/', views.LoginView.as_view(), name='api-login'),
    path('auth/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('me/', views.MeView.as_view(), name='api-me'),
    path('my-zone/', views.MyZoneView.as_view(), name='api-my-zone'),
    path('alerts/', views.AlertListView.as_view(), name='api-alerts'),
    path('alerts/<int:alert_id>/feedback/', views.AlertFeedbackView.as_view(), name='api-alert-feedback'),
]
