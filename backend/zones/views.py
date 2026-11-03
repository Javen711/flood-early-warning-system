from accounts.permissions import OfficerRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import ZoneForm
from .models import Zone


class ZoneListView(OfficerRequiredMixin, ListView):
    model = Zone
    template_name = 'zones/zone_list.html'
    context_object_name = 'zones'


class ZoneCreateView(OfficerRequiredMixin, CreateView):
    model = Zone
    form_class = ZoneForm
    template_name = 'zones/zone_form.html'
    success_url = reverse_lazy('zone-list')


class ZoneUpdateView(OfficerRequiredMixin, UpdateView):
    model = Zone
    form_class = ZoneForm
    template_name = 'zones/zone_form.html'
    success_url = reverse_lazy('zone-list')


class ZoneDeleteView(OfficerRequiredMixin, DeleteView):
    model = Zone
    template_name = 'zones/zone_confirm_delete.html'
    success_url = reverse_lazy('zone-list')
