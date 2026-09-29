from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import ZoneForm
from .models import Zone


class ZoneListView(LoginRequiredMixin, ListView):
    model = Zone
    template_name = 'zones/zone_list.html'
    context_object_name = 'zones'


class ZoneCreateView(LoginRequiredMixin, CreateView):
    model = Zone
    form_class = ZoneForm
    template_name = 'zones/zone_form.html'
    success_url = reverse_lazy('zone-list')


class ZoneUpdateView(LoginRequiredMixin, UpdateView):
    model = Zone
    form_class = ZoneForm
    template_name = 'zones/zone_form.html'
    success_url = reverse_lazy('zone-list')


class ZoneDeleteView(LoginRequiredMixin, DeleteView):
    model = Zone
    template_name = 'zones/zone_confirm_delete.html'
    success_url = reverse_lazy('zone-list')
