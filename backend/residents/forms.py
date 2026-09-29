from django import forms

from .models import Resident


class ResidentForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = ['full_name', 'phone_number', 'zone']
