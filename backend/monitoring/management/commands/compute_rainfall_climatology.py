import json
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from monitoring.climatology import summarise_climatology
from monitoring.openmeteo import OpenMeteoError
from monitoring.rainfall_history import build_history
from zones.models import Zone


class Command(BaseCommand):
    help = (
        "Measures how much rain Nairobi really gets (Open-Meteo history, 2015-2025) and saves the "
        "'heavy rain' level and the day-by-day history that train_flood_model then uses. Needs internet."
    )

    def handle(self, *args, **options):
        zones = list(Zone.objects.order_by('zone_name'))
        if not zones:
            raise CommandError("No zones found. Run `python manage.py load_nairobi_zones` first.")
        self.stdout.write("Fetching 11 years of daily rainfall for every zone. This takes a minute...")
        start, end = date(2015, 1, 1), date(2025, 12, 31)
        try:
            history, all_series = build_history(zones, start, end)
        except OpenMeteoError as exc:
            raise CommandError(f"{exc} (This command needs internet.)")
        result = summarise_climatology(all_series, start, end)

        path = settings.RAINFALL_CLIMATOLOGY_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(result, f, indent=2)

        p = result['percentiles_mm']
        self.stdout.write(self.style.SUCCESS(f"\nRainfall in Nairobi, {result['start']} to {result['end']}, {result['zones']} zones:"))
        self.stdout.write(f"  Days with at least 1 mm of rain: {result['wet_day_share'] * 100:.0f}%")
        self.stdout.write(f"  A typical wet day:               {result['median_wet_day_mm']} mm")
        self.stdout.write(f"  Heavy (top 10% of days):         {p['90']} mm")
        self.stdout.write(f"  Very heavy (top 5%):             {p['95']} mm")
        self.stdout.write(f"  Extreme (top 1%):                {p['99']} mm   <- used as the 'heavy rain' level")
        self.stdout.write(f"  Rarest (top 0.1%):               {p['99.9']} mm")
        self.stdout.write(f"  Wettest day on record:           {result['max_mm']} mm")
        history.to_csv(settings.RAINFALL_HISTORY_PATH, index=False)
        self.stdout.write(f"\nSaved to: {path}")
        self.stdout.write(f"Saved {len(history):,} zone-days of real rainfall (with the 3 days before each) to: {settings.RAINFALL_HISTORY_PATH}")
        self.stdout.write("Next: python manage.py train_flood_model --samples 5000   then   python manage.py backtest_flood_events")
