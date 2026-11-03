from django.contrib import messages
from accounts.permissions import OfficerRequiredMixin, officer_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView

from zones.models import Zone

from .forms import EnvironmentalDataForm
from .ml.predict import ModelNotTrainedError
from .models import EnvironmentalData
from . import weather
from .services import (
    NoCoordinatesError, NoDataError, fetch_live_reading_for_zone,
    run_prediction_for_zone, run_predictions_for_all_zones,
)


class EnvironmentalDataListView(OfficerRequiredMixin, ListView):
    model = EnvironmentalData
    template_name = 'monitoring/reading_list.html'
    context_object_name = 'readings'
    paginate_by = 25


class EnvironmentalDataCreateView(OfficerRequiredMixin, CreateView):
    model = EnvironmentalData
    form_class = EnvironmentalDataForm
    template_name = 'monitoring/reading_form.html'
    success_url = reverse_lazy('reading-list')


@officer_required
def run_prediction_for_zone_view(request, zone_id):
    """The dashboard's per-zone 'Run Prediction' button."""
    zone = get_object_or_404(Zone, pk=zone_id)
    try:
        prediction = run_prediction_for_zone(zone)
        messages.success(
            request,
            f"Prediction complete for {zone.zone_name}: {prediction.get_risk_level_display()} risk "
            f"({prediction.confidence_score:.0%} confidence).",
        )
    except NoDataError as exc:
        messages.warning(request, str(exc))
    except ModelNotTrainedError as exc:
        messages.error(request, str(exc))
    return redirect(reverse('dashboard'))


@officer_required
def run_predictions_for_all_zones_view(request):
    """The dashboard's 'Run predictions for all zones' button."""
    try:
        predictions, skipped = run_predictions_for_all_zones()
    except ModelNotTrainedError as exc:
        messages.error(request, str(exc))
        return redirect(reverse('dashboard'))

    if predictions:
        messages.success(request, f"Ran predictions for {len(predictions)} zone(s).")
    if skipped:
        messages.warning(
            request,
            "Skipped (no environmental data yet): " + ", ".join(z.zone_name for z in skipped),
        )
    if not predictions and not skipped:
        messages.info(request, "No zones exist yet. Add a zone first.")
    return redirect(reverse('dashboard'))


@officer_required
def fetch_weather_view(request):
    """The dashboard's 'Fetch live rainfall' button: updates every zone, then predicts."""
    if request.method != 'POST':
        return redirect(reverse('dashboard'))

    fetched, problems = [], []
    for zone in Zone.objects.all():
        try:
            reading = fetch_live_reading_for_zone(zone)
            fetched.append(f"{zone.zone_name} {reading.rainfall_mm} mm")
        except NoCoordinatesError:
            problems.append(f"{zone.zone_name} (no coordinates)")
        except weather.WeatherError as exc:
            problems.append(f"{zone.zone_name} ({exc})")
            break  # the service is unreachable; don't repeat the same failure per zone

    if fetched:
        messages.success(request, "Live rainfall saved: " + "; ".join(fetched) + ".")
        try:
            run_predictions_for_all_zones()
            messages.info(request, "Predictions were re-run with the new rainfall.")
        except ModelNotTrainedError as exc:
            messages.error(request, str(exc))
    if problems:
        messages.warning(request, "Not updated: " + ", ".join(problems))
    if not fetched and not problems:
        messages.info(request, "No zones exist yet. Add a zone first.")
    return redirect(reverse('dashboard'))
