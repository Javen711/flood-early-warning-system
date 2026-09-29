from django.conf import settings
from django.db import models

from zones.models import Zone


class EnvironmentalData(models.Model):
    """The ENVIRONMENTAL_DATA entity: one reading for one zone."""

    class Source(models.TextChoices):
        WEATHER_API = 'WEATHER_API', 'Weather data provider'
        SENSOR = 'SENSOR', 'Field / IoT sensor'
        MANUAL = 'MANUAL', 'Manual entry by field officer'

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='environmental_readings')
    rainfall_mm = models.DecimalField(max_digits=6, decimal_places=2)
    water_level_cm = models.DecimalField(max_digits=6, decimal_places=2)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.zone.zone_name} @ {self.recorded_at:%Y-%m-%d %H:%M}"


class AlertThreshold(models.Model):
    """The ALERT_THRESHOLD entity: an admin-configurable trigger value."""

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='thresholds')
    risk_parameter = models.CharField(
        max_length=50,
        default='rainfall_mm',
        help_text="Which reading this threshold applies to, e.g. rainfall_mm.",
    )
    threshold_value = models.DecimalField(max_digits=6, decimal_places=2)
    configured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='configured_thresholds',
    )

    class Meta:
        unique_together = ('zone', 'risk_parameter')

    def __str__(self):
        return f"{self.zone.zone_name}: {self.risk_parameter} > {self.threshold_value}"


class FloodPrediction(models.Model):
    """The FLOOD_PREDICTION entity: one ML model output for one zone."""

    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='predictions')
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4)
    model_version = models.CharField(max_length=50)
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-predicted_at']

    def __str__(self):
        return f"{self.zone.zone_name}: {self.risk_level} ({self.predicted_at:%Y-%m-%d %H:%M})"
