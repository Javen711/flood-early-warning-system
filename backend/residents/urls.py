from django.urls import path

from . import views

urlpatterns = [
    path('', views.ResidentListView.as_view(), name='resident-list'),
    path('add/', views.ResidentCreateView.as_view(), name='resident-add'),
    path('<int:pk>/edit/', views.ResidentUpdateView.as_view(), name='resident-edit'),
    path('<int:pk>/delete/', views.ResidentDeleteView.as_view(), name='resident-delete'),
]
