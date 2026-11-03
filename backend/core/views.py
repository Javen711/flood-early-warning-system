from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render

from accounts.permissions import officer_required

from monitoring.ml.predict import is_model_trained
from monitoring.models import FloodPrediction
from zones.models import Zone


def health_check(request):
    """
    Quick end-to-end check: confirms Django is running AND can reach the
    configured MySQL database. Visit /api/health/ once your .env and MySQL
    server are set up -- see backend/README.md.
    """
    db_status = "unknown"
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_status = "connected"
    except Exception as exc:
        db_status = "unreachable"
        db_error = str(exc)

    payload = {
        "service": "AFEWS backend",
        "status": "ok",
        "database": db_status,
    }
    if db_error:
        payload["database_error"] = db_error

    return JsonResponse(payload)


@login_required
def dashboard_view(request):
    # Residents have their own page; send them there without an error message.
    if request.user.is_resident:
        return redirect('portal')
    return _officer_dashboard(request)


@officer_required
def _officer_dashboard(request):
    """
    The main landing page after login: every zone with its most recent
    prediction, plus counts by risk level and the most recent alerts.
    """
    zones = list(Zone.objects.all().prefetch_related('predictions'))
    zone_rows = [
        {'zone': zone, 'prediction': zone.latest_prediction()}
        for zone in zones
    ]

    risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'UNKNOWN': 0}
    for row in zone_rows:
        prediction = row['prediction']
        risk_counts[prediction.risk_level if prediction else 'UNKNOWN'] += 1

    recent_alerts = (
        FloodPrediction.objects.filter(alerts__isnull=False)
        .distinct()
        .order_by('-predicted_at')[:10]
    )

    return render(request, 'dashboard.html', {
        'zone_rows': zone_rows,
        'risk_counts': risk_counts,
        'recent_alerts': recent_alerts,
        'model_is_trained': is_model_trained(),
    })
