from django.urls import path

from . import views

urlpatterns = [
    path('readings/', views.EnvironmentalDataListView.as_view(), name='reading-list'),
    path('readings/add/', views.EnvironmentalDataCreateView.as_view(), name='reading-add'),
    path('predict/<int:zone_id>/', views.run_prediction_for_zone_view, name='run-prediction'),
    path('predict-all/', views.run_predictions_for_all_zones_view, name='run-predictions-all'),
]
