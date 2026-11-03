from django.conf import settings
from django.db import models

from zones.models import Zone


class Resident(models.Model):
    """The RESIDENT entity: someone registered to receive flood alerts."""

    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='residents')
    registered_at = models.DateTimeField(auto_now_add=True)
    # Set when the resident creates their own login on the sign-up page.
    # Residents added by an officer have no login, so this stays empty.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='resident_profile',
    )

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.zone.zone_name})"
