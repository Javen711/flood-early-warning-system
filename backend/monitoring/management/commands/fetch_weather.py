from django.core.management.base import BaseCommand

from monitoring import weather
from monitoring.services import (
    NoCoordinatesError, fetch_live_reading_for_zone, run_predictions_for_all_zones,
)
from zones.models import Zone


class Command(BaseCommand):
    help = "Fetches live rainfall for every zone and saves it as a new reading."

    def add_arguments(self, parser):
        parser.add_argument('--predict', action='store_true', help="Re-run predictions afterwards.")

    def handle(self, *args, **options):
        saved = 0
        for zone in Zone.objects.all():
            try:
                reading = fetch_live_reading_for_zone(zone)
            except NoCoordinatesError as exc:
                self.stdout.write(self.style.WARNING(str(exc)))
                continue
            except weather.WeatherError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                return
            saved += 1
            self.stdout.write(f"{zone.zone_name}: rainfall {reading.rainfall_mm} mm, water level {reading.water_level_cm} cm")
        self.stdout.write(self.style.SUCCESS(f"Saved {saved} live reading(s)."))
        if options['predict'] and saved:
            predictions, _ = run_predictions_for_all_zones()
            for p in predictions:
                self.stdout.write(f"  {p.zone.zone_name}: {p.risk_level} ({p.confidence_score:.2f})")
