from django.core.management.base import BaseCommand

from monitoring.ml.predict import reset_cache
from monitoring.ml.train import train_and_save_model


class Command(BaseCommand):
    help = "Trains the Random Forest flood-risk model on synthetic data and saves it to disk."

    def add_arguments(self, parser):
        parser.add_argument('--samples', type=int, default=1200, help="Number of synthetic training rows to generate.")

    def handle(self, *args, **options):
        metadata = train_and_save_model(n_samples=options['samples'])
        reset_cache()

        self.stdout.write(self.style.SUCCESS(
            f"Trained model {metadata['model_version']} on {metadata['n_samples']} samples."
        ))
        self.stdout.write(f"Overall accuracy: {metadata['accuracy']:.3f}")
        self.stdout.write("Per-class metrics:")
        for label in metadata['labels']:
            row = metadata['classification_report'][label]
            self.stdout.write(
                f"  {label:>6}: precision={row['precision']:.2f}  "
                f"recall={row['recall']:.2f}  f1={row['f1-score']:.2f}  support={int(row['support'])}"
            )
        from django.conf import settings
        self.stdout.write(f"Model saved to: {settings.ML_MODEL_PATH}")
