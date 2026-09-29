from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Reuses Django's battle-tested UserAdmin (password hashing UI, etc.)
    and just adds our two extra fields to the display and edit forms."""

    list_display = ('username', 'full_name_display', 'role', 'contact_number', 'is_staff')
    list_filter = DjangoUserAdmin.list_filter + ('role',)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('AFEWS role', {'fields': ('role', 'contact_number')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('AFEWS role', {'fields': ('role', 'contact_number')}),
    )

    def full_name_display(self, obj):
        return obj.get_full_name()
    full_name_display.short_description = 'Full name'
