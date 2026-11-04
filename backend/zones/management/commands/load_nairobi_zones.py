from decimal import Decimal

from django.core.management.base import BaseCommand

from monitoring.models import EnvironmentalData
from zones.models import Zone
from zones.nairobi import NAIROBI_SUBCOUNTIES, OLD_DEMO_ZONE_NAMES


class Command(BaseCommand):
    help = (
        "Loads the 17 Nairobi sub-counties as zones (safe to re-run: existing ones are updated), "
        "removes the four old demo zones, and adds one starting reading per new zone."
    )

    def handle(self, *args, **options):
        old = Zone.objects.filter(zone_name__in=OLD_DEMO_ZONE_NAMES)
        removed = old.count()
        if removed:
            names = ", ".join(old.values_list('zone_name', flat=True))
            old.delete()  # also removes their demo residents, readings and alerts
            self.stdout.write(f"Removed {removed} old demo zone(s): {names}")

        created = updated = 0
        for name, wards, elevation, drainage, lat, lon, rainfall, water in NAIROBI_SUBCOUNTIES:
            zone, was_created = Zone.objects.update_or_create(
                zone_name=name,
                defaults={
                    'ward': wards, 'elevation_m': Decimal(elevation), 'drainage_quality': drainage,
                    'latitude': Decimal(str(lat)), 'longitude': Decimal(str(lon)),
                },
            )
            if was_created:
                created += 1
                EnvironmentalData.objects.create(
                    zone=zone, rainfall_mm=Decimal(rainfall), water_level_cm=Decimal(water),
                    source=EnvironmentalData.Source.MANUAL,
                )
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Zones ready: {created} created, {updated} updated ({len(NAIROBI_SUBCOUNTIES)} in total)."
        ))
        self.stdout.write("Next: python manage.py run_flood_predictions")
