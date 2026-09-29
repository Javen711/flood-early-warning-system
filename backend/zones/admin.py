from django.contrib import admin

from .models import Zone


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('zone_name', 'ward', 'elevation_m', 'drainage_quality', 'created_at')
    list_filter = ('drainage_quality',)
    search_fields = ('zone_name', 'ward')
