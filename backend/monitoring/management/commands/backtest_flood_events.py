from django.core.management.base import BaseCommand, CommandError

from monitoring.backtest import BacktestError, EVENTS, RIVER_LEVELS, fetch_conditions, run_backtest, summarise
from monitoring.ml.predict import ModelNotTrainedError, predict_risk
from zones.models import Zone


class Command(BaseCommand):
    help = (
        "Checks the trained model against real Nairobi flood days, using real rainfall "
        "from Open-Meteo's history. Needs internet. Run train_flood_model first."
    )

    def handle(self, *args, **options):
        zones = list(Zone.objects.order_by('zone_name'))
        if not zones:
            raise CommandError("No zones found. Run `python manage.py load_nairobi_zones` first.")
        try:
            results = run_backtest(zones, EVENTS, fetch_conditions, predict_risk)
        except ModelNotTrainedError as exc:
            raise CommandError(str(exc))
        except BacktestError as exc:
            raise CommandError(f"{exc} (This command needs internet.)")

        levels = ', '.join(f"{name} {cm} cm" for name, cm in RIVER_LEVELS)
        self.stdout.write(f"River level is unknown for past dates, so each case is run at: {levels}.\n")

        for result in results:
            event = result['event']
            self.stdout.write(self.style.SUCCESS(f"\n{event['label']}"))
            if event['what']:
                self.stdout.write(f"  What happened: {event['what']}")
            if event['source']:
                self.stdout.write(f"  Source: {event['source']}")
            if event.get('note'):
                self.stdout.write(f"  Note: {event['note']}")
            if event.get('gauge_mm') and result['rows']:
                reported = [r for r in result['rows'] if r['reported']] or result['rows']
                self.stdout.write(
                    f"  Rain gauge reported {event['gauge_mm']} mm in 24 hours; "
                    f"the Open-Meteo grid says {reported[0]['rain_mm']:.1f} mm for {reported[0]['zone']}."
                )
            self.stdout.write(f"  {'Zone':<30}{'Rain mm':>8}{'3d before':>10}   " + '   '.join(f"{n:<9}" for n, _ in RIVER_LEVELS) + "  Reported flooded?")
            for row in sorted(result['rows'], key=lambda r: (not r['reported'], r['zone'])):
                if event['kind'] == 'flood' and not row['reported']:
                    note = 'not reported'
                elif event['kind'] == 'flood':
                    note = 'YES'
                else:
                    note = '-'
                cells = '   '.join(f"{row['levels'][n]:<9}" for n, _ in RIVER_LEVELS)
                self.stdout.write(f"  {row['zone']:<30}{row['rain_mm']:>8.1f}{row['antecedent_mm']:>10.1f}   {cells}  {note}")

        self.stdout.write(self.style.SUCCESS("\nSummary at a moderate river level (60 cm), flagged = MEDIUM or HIGH:"))
        for result in results:
            event, s = result['event'], summarise(result, 'moderate')
            if event['kind'] == 'flood':
                self.stdout.write(
                    f"  {event['label']}: rain {s['max_rain_mm']:.0f} mm, flagged {s['reported_flagged']} of "
                    f"{s['reported_total']} reported zones ({s['reported_high']} as HIGH)."
                )
            else:
                self.stdout.write(
                    f"  {event['label']}: rain {s['max_rain_mm']:.0f} mm, flagged {s['others_flagged']} of "
                    f"{s['others_total']} zones (false alarms if no flood happened)."
                )
        floods = [(r['event'], summarise(r, 'moderate')) for r in results if r['event']['kind'] == 'flood']
        total = sum(s['reported_total'] for _, s in floods)
        flagged = sum(s['reported_flagged'] for _, s in floods)
        high = sum(s['reported_high'] for _, s in floods)
        self.stdout.write(self.style.SUCCESS(
            f"\nAcross all {len(floods)} flood events: {flagged} of {total} reported zone-cases flagged "
            f"({high} as HIGH) at a 60 cm river."
        ))
        self.stdout.write(
            "\nRainfall is gridded data (roughly 10 km), so nearby zones get similar rain; "
            "what separates them is elevation and drainage."
        )
