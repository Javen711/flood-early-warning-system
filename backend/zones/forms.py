from django import forms

from .models import Zone


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['zone_name', 'ward', 'elevation_m', 'drainage_quality', 'geo_boundary']
        widgets = {
            'geo_boundary': forms.Textarea(attrs={'rows': 3}),
        }
