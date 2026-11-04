"""
Loads the 17 Nairobi sub-counties (via load_nairobi_zones) and a couple of demo
residents in each, so the dashboard has something to show after a fresh
`migrate`. Safe to re-run.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from residents.models import Resident
from zones.models import Zone

DEMO_RESIDENTS_PER_ZONE = [
    ("Amina Wanjiru", "+254700111222"),
    ("Brian Otieno", "+254700333444"),
]


class Command(BaseCommand):
    help = "Loads the Nairobi sub-county zones plus demo residents."

    def handle(self, *args, **options):
        call_command('load_nairobi_zones', stdout=self.stdout)
        for zone in Zone.objects.all():
            for full_name, phone in DEMO_RESIDENTS_PER_ZONE:
                Resident.objects.get_or_create(
                    full_name=full_name, zone=zone, defaults={'phone_number': phone},
                )
        self.stdout.write(self.style.SUCCESS("Demo residents added."))
        self.stdout.write("Next: python manage.py train_flood_model, then python manage.py run_flood_predictions")
