"""
The orchestration layer for the ML pipeline: takes a zone's latest reading,
runs it through the trained model, records the prediction, and — if the
risk is Medium or High — raises an alert and logs a (simulated) delivery
to every resident registered in that zone.

This is what the sequence diagram "Generate & Send Flood Alert" describes,
minus the real SMS gateway integration (that's Phase 6).
"""
from .ml.predict import predict_risk
from .models import EnvironmentalData, FloodPrediction


class NoDataError(RuntimeError):
    """Raised when a zone has no environmental readings to predict from."""


def run_prediction_for_zone(zone) -> FloodPrediction:
    """
    Pulls the zone's most recent EnvironmentalData row, runs the model,
    saves a FloodPrediction, and (for Medium/High risk) creates an Alert
    with a simulated delivery to every resident in the zone.
    """
    # Import here, not at module load time, to avoid a circular import:
    # alerts.models imports monitoring.models, so monitoring can't import
    # alerts.models at the top of this file.
    from alerts.models import Alert, AlertDelivery

    latest_reading = zone.environmental_readings.order_by('-recorded_at').first()
    if latest_reading is None:
        raise NoDataError(
            f"Zone '{zone.zone_name}' has no environmental data yet. "
            "Add a reading before running a prediction."
        )

    risk_level, confidence_score, model_version = predict_risk(
        rainfall_mm=latest_reading.rainfall_mm,
        antecedent_rain_mm=latest_reading.antecedent_rain_mm,
        water_level_cm=latest_reading.water_level_cm,
        elevation_m=zone.elevation_m,
        drainage_quality=zone.drainage_quality,
    )

    prediction = FloodPrediction.objects.create(
        zone=zone,
        risk_level=risk_level,
        confidence_score=confidence_score,
        model_version=model_version,
    )

    if risk_level in (FloodPrediction.RiskLevel.MEDIUM, FloodPrediction.RiskLevel.HIGH):
        alert = Alert.objects.create(
            prediction=prediction,
            message=(
                f"{risk_level.title()} flood risk detected in {zone.zone_name}. "
                f"Please take precaution and follow local guidance."
            ),
            channel=Alert.Channel.SMS,
        )
        residents = zone.residents.all()
        AlertDelivery.objects.bulk_create([
            AlertDelivery(alert=alert, resident=resident, delivery_status=AlertDelivery.DeliveryStatus.SIMULATED)
            for resident in residents
        ])

    return prediction


def run_predictions_for_all_zones():
    """Runs run_prediction_for_zone for every zone that has data, skipping
    (and reporting) any that don't yet."""
    from zones.models import Zone

    results = []
    skipped = []
    for zone in Zone.objects.all():
        try:
            results.append(run_prediction_for_zone(zone))
        except NoDataError:
            skipped.append(zone)
    return results, skipped


class NoCoordinatesError(RuntimeError):
    """Raised when a zone has no latitude/longitude, so weather can't be fetched."""


def fetch_live_reading_for_zone(zone):
    """
    Pulls current rainfall from the weather service and saves it as a new
    EnvironmentalData row (source = WEATHER_API).

    The weather service has no water-level data, so the zone's most recent
    water level is carried forward (0 if the zone has no readings yet).
    """
    from . import weather
    from .models import EnvironmentalData

    if not zone.has_coordinates:
        raise NoCoordinatesError(
            f"Zone '{zone.zone_name}' has no latitude/longitude. Edit the zone and add them."
        )
    rainfall_mm, antecedent_rain_mm = weather.get_recent_conditions(zone.latitude, zone.longitude)
    previous = zone.environmental_readings.order_by('-recorded_at').first()
    water_level_cm = previous.water_level_cm if previous else 0
    return EnvironmentalData.objects.create(
        zone=zone,
        rainfall_mm=round(rainfall_mm, 2),
        antecedent_rain_mm=round(antecedent_rain_mm, 2),
        water_level_cm=water_level_cm,
        source=EnvironmentalData.Source.WEATHER_API,
    )
