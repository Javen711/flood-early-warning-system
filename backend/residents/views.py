from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import ResidentForm
from .models import Resident


class ResidentListView(LoginRequiredMixin, ListView):
    model = Resident
    template_name = 'residents/resident_list.html'
    context_object_name = 'residents'


class ResidentCreateView(LoginRequiredMixin, CreateView):
    model = Resident
    form_class = ResidentForm
    template_name = 'residents/resident_form.html'
    success_url = reverse_lazy('resident-list')


class ResidentUpdateView(LoginRequiredMixin, UpdateView):
    model = Resident
    form_class = ResidentForm
    template_name = 'residents/resident_form.html'
    success_url = reverse_lazy('resident-list')


class ResidentDeleteView(LoginRequiredMixin, DeleteView):
    model = Resident
    template_name = 'residents/resident_confirm_delete.html'
    success_url = reverse_lazy('resident-list')
