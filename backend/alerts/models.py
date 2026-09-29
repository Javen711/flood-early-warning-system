from django.db import models

from monitoring.models import FloodPrediction
from residents.models import Resident


class Alert(models.Model):
    """The ALERT entity: one message generated from one prediction."""

    class Channel(models.TextChoices):
        SMS = 'SMS', 'SMS'
        APP = 'APP', 'Mobile app push'
        DASHBOARD = 'DASHBOARD', 'Dashboard only'

    prediction = models.ForeignKey(FloodPrediction, on_delete=models.CASCADE, related_name='alerts')
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.DASHBOARD)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Alert for {self.prediction.zone.zone_name}: {self.prediction.risk_level}"


class AlertDelivery(models.Model):
    """
    The ALERT_DELIVERY entity: the junction between one alert and one
    resident who should receive it, tracking whether it actually got there.
    In this phase, an SMS gateway isn't wired up yet (that's Phase 6), so
    delivery_status stays PENDING/SIMULATED until that integration exists.
    """

    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SIMULATED = 'SIMULATED', 'Simulated (no SMS gateway connected yet)'
        DELIVERED = 'DELIVERED', 'Delivered'
        FAILED = 'FAILED', 'Failed'

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='deliveries')
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='alert_deliveries')
    delivery_status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('alert', 'resident')

    def __str__(self):
        return f"{self.resident.full_name} <- {self.alert} [{self.delivery_status}]"


class Feedback(models.Model):
    """The FEEDBACK entity: a resident's response to an alert they received."""

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='feedback_entries')
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='feedback_entries')
    comment = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        help_text="1 (not useful) to 5 (very useful)",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Feedback from {self.resident.full_name} ({self.rating}/5)"
