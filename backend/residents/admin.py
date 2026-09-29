from django.contrib import admin

from .models import Resident


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'zone', 'registered_at')
    list_filter = ('zone',)
    search_fields = ('full_name', 'phone_number')
