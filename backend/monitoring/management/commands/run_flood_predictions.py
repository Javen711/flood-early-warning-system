from django.core.management.base import BaseCommand

from monitoring.services import run_predictions_for_all_zones


class Command(BaseCommand):
    help = "Runs the flood-risk model against every zone's latest reading and stores the predictions."

    def handle(self, *args, **options):
        predictions, skipped = run_predictions_for_all_zones()

        for prediction in predictions:
            self.stdout.write(
                f"{prediction.zone.zone_name}: {prediction.risk_level} "
                f"(confidence {prediction.confidence_score:.2f})"
            )
        if skipped:
            self.stdout.write(self.style.WARNING(
                "Skipped (no environmental data yet): " + ", ".join(z.zone_name for z in skipped)
            ))
        if not predictions and not skipped:
            self.stdout.write(self.style.WARNING("No zones found. Add a zone first."))
