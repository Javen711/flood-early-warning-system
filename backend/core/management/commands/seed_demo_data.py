"""
Creates a handful of realistic zones, residents and environmental readings
so the dashboard has something to show right after a fresh `migrate` --
useful for a supervisor demo, and safe to re-run (it won't duplicate zones
it already created).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from monitoring.models import EnvironmentalData
from residents.models import Resident
from zones.models import Zone

DEMO_ZONES = [
    # name, ward, elevation_m, drainage_quality, rainfall_mm, water_level_cm
    ("Kibera - Gatwekera", "Kibera", Decimal("15.0"), Zone.DrainageQuality.POOR, Decimal("140"), Decimal("95")),
    ("Mathare 4A", "Mathare", Decimal("18.5"), Zone.DrainageQuality.POOR, Decimal("60"), Decimal("40")),
    ("Mukuru Kwa Njenga", "Mukuru", Decimal("22.0"), Zone.DrainageQuality.MODERATE, Decimal("30"), Decimal("15")),
    ("Kawangware", "Kawangware", Decimal("35.0"), Zone.DrainageQuality.GOOD, Decimal("10"), Decimal("5")),
]

# Approximate centre of each demo zone, used for live weather lookups.
DEMO_COORDINATES = {
    "Kibera - Gatwekera": (Decimal("-1.3133"), Decimal("36.7876")),
    "Mathare 4A": (Decimal("-1.2597"), Decimal("36.8584")),
    "Mukuru Kwa Njenga": (Decimal("-1.3141"), Decimal("36.8664")),
    "Kawangware": (Decimal("-1.2833"), Decimal("36.7467")),
}

DEMO_RESIDENTS_PER_ZONE = [
    ("Amina Wanjiru", "+254700111222"),
    ("Brian Otieno", "+254700333444"),
]


class Command(BaseCommand):
    help = "Seeds a handful of demo zones, residents and environmental readings."

    def handle(self, *args, **options):
        created_zones = 0
        for name, ward, elevation, drainage, rainfall, water_level in DEMO_ZONES:
            zone, was_created = Zone.objects.get_or_create(
                zone_name=name,
                defaults={'ward': ward, 'elevation_m': elevation, 'drainage_quality': drainage},
            )
            if was_created:
                created_zones += 1
            if not zone.has_coordinates and name in DEMO_COORDINATES:
                zone.latitude, zone.longitude = DEMO_COORDINATES[name]
                zone.save(update_fields=['latitude', 'longitude'])

            EnvironmentalData.objects.create(
                zone=zone,
                rainfall_mm=rainfall,
                water_level_cm=water_level,
                source=EnvironmentalData.Source.MANUAL,
            )

            for full_name, phone in DEMO_RESIDENTS_PER_ZONE:
                Resident.objects.get_or_create(
                    full_name=full_name, zone=zone, defaults={'phone_number': phone},
                )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created_zones} new zone(s) (existing zones were left as-is), "
            f"each with a fresh environmental reading and demo residents."
        ))
        self.stdout.write("Next: python manage.py train_flood_model, then python manage.py run_flood_predictions")
