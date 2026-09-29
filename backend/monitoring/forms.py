from django import forms

from .models import EnvironmentalData


class EnvironmentalDataForm(forms.ModelForm):
    class Meta:
        model = EnvironmentalData
        fields = ['zone', 'rainfall_mm', 'water_level_cm', 'source']
