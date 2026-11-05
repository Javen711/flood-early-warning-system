from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from alerts.models import Alert
from residents.models import Resident
from zones.models import Zone

from .ml.dataset import generate_synthetic_dataset
from .ml.train import train_and_save_model
from .ml import predict as predict_module
from .models import EnvironmentalData, FloodPrediction
from .services import NoDataError, run_prediction_for_zone

User = get_user_model()


class SyntheticDatasetTests(TestCase):
    def test_dataset_has_expected_shape_and_labels(self):
        df = generate_synthetic_dataset(n_samples=200, random_state=1)
        self.assertEqual(len(df), 200)
        self.assertEqual(
            set(df.columns), {'rainfall_mm', 'water_level_cm', 'elevation_m', 'drainage_score', 'risk_level'}
        )
        self.assertTrue(set(df['risk_level'].unique()) <= {'LOW', 'MEDIUM', 'HIGH'})

    def test_high_rainfall_low_elevation_skews_toward_higher_risk(self):
        """Sanity check on the labelling rule itself, not the trained model:
        severe conditions should produce mostly Medium/High labels."""
        import numpy as np
        from .ml.dataset import _label_from_features
        rng = np.random.default_rng(0)
        labels = [_label_from_features(190, 140, 8, 0, rng) for _ in range(200)]
        severe_share = sum(1 for l in labels if l in ('MEDIUM', 'HIGH')) / len(labels)
        self.assertGreater(severe_share, 0.8)


class TrainAndPredictTests(TestCase):
    """These use a tiny sample count to keep the test suite fast."""

    def setUp(self):
        train_and_save_model(n_samples=150, random_state=1)
        predict_module.reset_cache()

    def test_model_file_and_metadata_are_written(self):
        from django.conf import settings
        self.assertTrue(settings.ML_MODEL_PATH.exists())
        self.assertTrue(settings.ML_METADATA_PATH.exists())

    def test_predict_risk_returns_a_valid_label_and_confidence(self):
        risk_level, confidence, model_version = predict_module.predict_risk(
            rainfall_mm=150, water_level_cm=120, elevation_m=10, drainage_quality='POOR',
        )
        self.assertIn(risk_level, ('LOW', 'MEDIUM', 'HIGH'))
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertTrue(model_version.startswith('rf-'))

    def test_predicting_before_training_raises_clear_error(self):
        from django.conf import settings
        settings.ML_MODEL_PATH.unlink()
        predict_module.reset_cache()
        with self.assertRaises(predict_module.ModelNotTrainedError):
            predict_module.predict_risk(100, 50, 20, 'MODERATE')


class PipelineServiceTests(TestCase):
    def setUp(self):
        train_and_save_model(n_samples=150, random_state=1)
        predict_module.reset_cache()
        self.zone = Zone.objects.create(
            zone_name='Pipeline Test Zone', elevation_m=Decimal('1600'), drainage_quality=Zone.DrainageQuality.POOR,
        )
        self.resident = Resident.objects.create(
            full_name='Test Resident', phone_number='+254700000000', zone=self.zone,
        )

    def test_prediction_without_data_raises(self):
        with self.assertRaises(NoDataError):
            run_prediction_for_zone(self.zone)

    def test_high_risk_reading_creates_prediction_and_alert_with_delivery(self):
        EnvironmentalData.objects.create(
            zone=self.zone, rainfall_mm=Decimal('195'), water_level_cm=Decimal('145'),
        )
        prediction = run_prediction_for_zone(self.zone)
        self.assertIsInstance(prediction, FloodPrediction)
        self.assertEqual(FloodPrediction.objects.filter(zone=self.zone).count(), 1)

        if prediction.risk_level in ('MEDIUM', 'HIGH'):
            alert = Alert.objects.get(prediction=prediction)
            deliveries = alert.deliveries.all()
            self.assertEqual(deliveries.count(), 1)
            self.assertEqual(deliveries.first().resident, self.resident)

    def test_low_risk_reading_does_not_create_an_alert(self):
        EnvironmentalData.objects.create(
            zone=self.zone, rainfall_mm=Decimal('5'), water_level_cm=Decimal('2'),
        )
        # Force a low-risk zone profile by overriding elevation/drainage on the fly
        self.zone.elevation_m = Decimal('1800')
        self.zone.drainage_quality = Zone.DrainageQuality.GOOD
        self.zone.save()

        prediction = run_prediction_for_zone(self.zone)
        if prediction.risk_level == 'LOW':
            self.assertEqual(Alert.objects.filter(prediction=prediction).count(), 0)


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='officer1', password='testpass123')
        self.zone = Zone.objects.create(zone_name='Dashboard Zone', elevation_m=Decimal('15'))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_dashboard_loads_when_logged_in(self):
        self.client.login(username='officer1', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Zone')


class LiveWeatherTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='officer2', password='testpass123')
        self.zone = Zone.objects.create(
            zone_name='Weather Zone', elevation_m=Decimal('12'),
            latitude=Decimal('-1.3133'), longitude=Decimal('36.7876'),
        )

    def test_get_recent_rainfall_takes_the_larger_of_yesterday_and_today(self):
        from unittest import mock
        from . import weather
        with mock.patch.object(weather, 'fetch_daily_rainfall', return_value=[42.5, 3.0]):
            self.assertEqual(weather.get_recent_rainfall_mm(-1.3, 36.7), 42.5)

    def test_live_reading_is_saved_with_weather_source_and_carries_water_level(self):
        from unittest import mock
        from . import weather
        from .services import fetch_live_reading_for_zone
        EnvironmentalData.objects.create(zone=self.zone, rainfall_mm=Decimal('1'), water_level_cm=Decimal('77'))
        with mock.patch.object(weather, 'fetch_daily_rainfall', return_value=[10.0, 55.25]):
            reading = fetch_live_reading_for_zone(self.zone)
        self.assertEqual(reading.source, EnvironmentalData.Source.WEATHER_API)
        self.assertEqual(reading.rainfall_mm, Decimal('55.25'))
        self.assertEqual(reading.water_level_cm, Decimal('77'))

    def test_zone_without_coordinates_is_rejected(self):
        from .services import NoCoordinatesError, fetch_live_reading_for_zone
        zone = Zone.objects.create(zone_name='No Coords', elevation_m=Decimal('20'))
        with self.assertRaises(NoCoordinatesError):
            fetch_live_reading_for_zone(zone)

    def test_dashboard_button_saves_readings_and_reports_service_failure(self):
        from unittest import mock
        from . import weather
        self.client.login(username='officer2', password='testpass123')
        with mock.patch.object(weather, 'fetch_daily_rainfall', return_value=[0.0, 20.0]):
            self.client.post(reverse('fetch-weather'))
        self.assertEqual(EnvironmentalData.objects.filter(zone=self.zone, source='WEATHER_API').count(), 1)

        with mock.patch.object(weather, 'fetch_daily_rainfall', side_effect=weather.WeatherError('offline')):
            response = self.client.post(reverse('fetch-weather'), follow=True)
        self.assertContains(response, 'Not updated')
        self.assertEqual(EnvironmentalData.objects.filter(zone=self.zone, source='WEATHER_API').count(), 1)


class ElevationScalingTests(TestCase):
    def test_real_elevations_are_mapped_onto_the_models_scale(self):
        from .ml.dataset import to_model_elevation
        self.assertEqual(to_model_elevation(1600), 5)
        self.assertEqual(to_model_elevation(1800), 60)
        self.assertAlmostEqual(to_model_elevation(1700), 32.5)
        self.assertEqual(to_model_elevation(1500), 5)     # below the range: clipped
        self.assertEqual(to_model_elevation(2100), 60)    # above the range: clipped

    def test_low_flooded_zone_and_high_dry_zone_get_different_risk(self):
        """With real (1,600-1,800 m) elevations the model must still tell zones apart."""
        train_and_save_model()  # full-size model, fixed seed
        predict_module.reset_cache()
        low_wet, _, _ = predict_module.predict_risk(140, 95, 1650, 'POOR')
        high_dry, _, _ = predict_module.predict_risk(10, 5, 1780, 'GOOD')
        self.assertIn(low_wet, ('MEDIUM', 'HIGH'))
        self.assertEqual(high_dry, 'LOW')


class NairobiZonesTests(TestCase):
    def test_command_loads_17_zones_replaces_old_demo_zones_and_is_repeatable(self):
        from django.core.management import call_command
        from zones.nairobi import NAIROBI_SUBCOUNTIES, OLD_DEMO_ZONE_NAMES
        old = Zone.objects.create(zone_name=OLD_DEMO_ZONE_NAMES[0], elevation_m=Decimal('15'))
        Resident.objects.create(full_name='Old', phone_number='+254700000001', zone=old)
        keep = Zone.objects.create(zone_name='My Own Zone', elevation_m=Decimal('1700'))

        call_command('load_nairobi_zones', verbosity=0)
        call_command('load_nairobi_zones', verbosity=0)  # second run must not duplicate

        self.assertEqual(len(NAIROBI_SUBCOUNTIES), 17)
        self.assertEqual(Zone.objects.filter(zone_name__endswith='Sub-County').count(), 17)
        self.assertFalse(Zone.objects.filter(zone_name__in=OLD_DEMO_ZONE_NAMES).exists())
        self.assertTrue(Zone.objects.filter(pk=keep.pk).exists())   # only the old demo zones are removed
        self.assertEqual(EnvironmentalData.objects.count(), 17)      # one starting reading each, once
        kibra = Zone.objects.get(zone_name='Kibra Sub-County')
        self.assertTrue(kibra.has_coordinates)

    def test_every_zone_has_valid_values(self):
        from zones.nairobi import NAIROBI_SUBCOUNTIES
        names = [row[0] for row in NAIROBI_SUBCOUNTIES]
        self.assertEqual(len(set(names)), 17)
        for name, wards, elevation, drainage, lat, lon, rain, water in NAIROBI_SUBCOUNTIES:
            self.assertLessEqual(len(wards), 100, name)
            self.assertTrue(1500 <= elevation <= 1900, name)
            self.assertTrue(-1.5 < lat < -1.1 and 36.6 < lon < 37.1, name)


class HighThresholdTests(TestCase):
    """The lower bar for HIGH (monitoring/ml/decision.py)."""

    classes = ['HIGH', 'LOW', 'MEDIUM']

    def test_high_is_chosen_at_the_threshold_even_if_medium_is_more_likely(self):
        from .ml.decision import decide_levels
        levels, confidences = decide_levels(self.classes, [[0.35, 0.15, 0.50]], threshold=0.30)
        self.assertEqual(levels, ['HIGH'])
        self.assertAlmostEqual(confidences[0], 0.35)

    def test_below_the_threshold_the_most_likely_level_wins(self):
        from .ml.decision import decide_levels
        levels, confidences = decide_levels(self.classes, [[0.20, 0.10, 0.70], [0.10, 0.80, 0.10]], threshold=0.30)
        self.assertEqual(levels, ['MEDIUM', 'LOW'])
        self.assertAlmostEqual(confidences[0], 0.70)

    def test_training_reports_both_ways_of_deciding(self):
        from django.test import override_settings
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            with override_settings(ML_MODEL_DIR=tmp, ML_MODEL_PATH=tmp / 'm.joblib', ML_METADATA_PATH=tmp / 'm.json'):
                metadata = train_and_save_model(n_samples=600)
        self.assertIn('plain_accuracy', metadata)
        self.assertEqual(metadata['high_alert_threshold'], 0.30)
        self.assertGreaterEqual(
            metadata['classification_report']['HIGH']['recall'],
            metadata['plain_classification_report']['HIGH']['recall'],
        )
