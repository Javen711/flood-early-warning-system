from django.contrib import admin

from .models import Alert, AlertDelivery, Feedback


class AlertDeliveryInline(admin.TabularInline):
    model = AlertDelivery
    extra = 0


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('prediction', 'channel', 'sent_at')
    list_filter = ('channel',)
    inlines = [AlertDeliveryInline]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('resident', 'alert', 'rating', 'submitted_at')
