from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='environmentaldata',
            name='antecedent_rain_mm',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=6,
                help_text='Total rain over the 3 days before the rainfall figure (how wet the ground already is). 0 if unknown.',
            ),
        ),
    ]
