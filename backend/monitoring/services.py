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
