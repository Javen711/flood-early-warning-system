from django.urls import path

from . import views

urlpatterns = [
    path('', views.ZoneListView.as_view(), name='zone-list'),
    path('add/', views.ZoneCreateView.as_view(), name='zone-add'),
    path('<int:pk>/edit/', views.ZoneUpdateView.as_view(), name='zone-edit'),
    path('<int:pk>/delete/', views.ZoneDeleteView.as_view(), name='zone-delete'),
]
