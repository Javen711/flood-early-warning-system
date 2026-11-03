import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from residents.models import Resident
from zones.models import Zone

from .models import User


def normalise_phone(raw):
    """Turns 0712 345 678 or +254 712 345 678 into +254712345678."""
    cleaned = re.sub(r'[\s\-()]', '', raw or '')
    if cleaned.startswith('0') and len(cleaned) == 10:
        cleaned = '+254' + cleaned[1:]
    elif cleaned.startswith('254'):
        cleaned = '+' + cleaned
    if not re.fullmatch(r'\+\d{9,15}', cleaned):
        raise forms.ValidationError(
            "Enter a phone number like 0712 345 678 or +254 712 345 678."
        )
    return cleaned


class ResidentSignUpForm(UserCreationForm):
    """
    Self-service registration for residents. The role is never taken from
    the form: every account created here is a RESIDENT, so nobody can sign
    themselves up as an officer.
    """

    full_name = forms.CharField(max_length=150, label="Full name")
    phone_number = forms.CharField(max_length=20, label="Phone number",
                                   help_text="Flood alerts are sent to this number.")
    zone = forms.ModelChoiceField(queryset=Zone.objects.none(), label="Your zone",
                                  empty_label="Choose your area")

    class Meta:
        model = User
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zone'].queryset = Zone.objects.all()
        self.order_fields(['full_name', 'phone_number', 'zone', 'username', 'password1', 'password2'])

    def clean_phone_number(self):
        return normalise_phone(self.cleaned_data['phone_number'])

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data['full_name'].strip()
        first, _, last = full_name.partition(' ')
        user.first_name, user.last_name = first, last
        user.role = User.Role.RESIDENT
        user.contact_number = self.cleaned_data['phone_number']
        user.save()

        zone = self.cleaned_data['zone']
        phone = self.cleaned_data['phone_number']
        # If an officer already registered this phone number in this zone,
        # attach the login to that record instead of creating a duplicate.
        # (Alerts are addressed to Resident records, so there must be one each.)
        existing = Resident.objects.filter(zone=zone, phone_number=phone, user__isnull=True).first()
        if existing:
            existing.user = user
            existing.save(update_fields=['user'])
        else:
            Resident.objects.create(full_name=full_name, phone_number=phone, zone=zone, user=user)
        return user
