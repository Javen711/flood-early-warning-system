from django.db import models


class Zone(models.Model):
    """The ZONE entity: a monitored informal-settlement area."""

    class DrainageQuality(models.TextChoices):
        POOR = 'POOR', 'Poor'
        MODERATE = 'MODERATE', 'Moderate'
        GOOD = 'GOOD', 'Good'

    zone_name = models.CharField(max_length=100, unique=True)
    ward = models.CharField(max_length=100, blank=True)
    elevation_m = models.DecimalField(
        max_digits=7, decimal_places=2,
        help_text="Average elevation of the zone above sea level, in metres.",
    )
    drainage_quality = models.CharField(
        max_length=10, choices=DrainageQuality.choices, default=DrainageQuality.MODERATE,
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Zone centre latitude (e.g. -1.3133). Needed to fetch live weather.",
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Zone centre longitude (e.g. 36.7876). Needed to fetch live weather.",
    )
    # Kept as a simple text field for now (e.g. a GeoJSON polygon or a
    # description). A dedicated GIS field type can replace this later
    # without breaking anything relying on this model.
    geo_boundary = models.TextField(
        blank=True,
        help_text="Optional GeoJSON (or plain description) of the zone's boundary.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['zone_name']

    def __str__(self):
        return self.zone_name

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    def latest_prediction(self):
        """Convenience helper used by the dashboard template."""
        return self.predictions.order_by('-predicted_at').first()
