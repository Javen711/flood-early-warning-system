from django.contrib import admin

from .models import AlertThreshold, EnvironmentalData, FloodPrediction


@admin.register(EnvironmentalData)
class EnvironmentalDataAdmin(admin.ModelAdmin):
    list_display = ('zone', 'rainfall_mm', 'water_level_cm', 'source', 'recorded_at')
    list_filter = ('source', 'zone')


@admin.register(AlertThreshold)
class AlertThresholdAdmin(admin.ModelAdmin):
    list_display = ('zone', 'risk_parameter', 'threshold_value', 'configured_by')


@admin.register(FloodPrediction)
class FloodPredictionAdmin(admin.ModelAdmin):
    list_display = ('zone', 'risk_level', 'confidence_score', 'model_version', 'predicted_at')
    list_filter = ('risk_level',)
