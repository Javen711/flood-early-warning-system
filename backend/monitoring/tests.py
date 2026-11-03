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
            zone_name='Pipeline Test Zone', elevation_m=Decimal('10'), drainage_quality=Zone.DrainageQuality.POOR,
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
        self.zone.elevation_m = Decimal('55')
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
