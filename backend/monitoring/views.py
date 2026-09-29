from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView

from zones.models import Zone

from .forms import EnvironmentalDataForm
from .ml.predict import ModelNotTrainedError
from .models import EnvironmentalData
from .services import NoDataError, run_prediction_for_zone, run_predictions_for_all_zones


class EnvironmentalDataListView(LoginRequiredMixin, ListView):
    model = EnvironmentalData
    template_name = 'monitoring/reading_list.html'
    context_object_name = 'readings'
    paginate_by = 25


class EnvironmentalDataCreateView(LoginRequiredMixin, CreateView):
    model = EnvironmentalData
    form_class = EnvironmentalDataForm
    template_name = 'monitoring/reading_form.html'
    success_url = reverse_lazy('reading-list')


@login_required
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


@login_required
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
