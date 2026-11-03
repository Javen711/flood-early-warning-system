"""
Who may open which screen.

Officers, admins and superusers can use the dashboard and the management
screens. Residents (self-registered) can only see their own page. Anyone
not logged in is sent to the login page.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def _deny(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    messages.warning(request, "That page is for disaster management officers.")
    return redirect('portal')


class OfficerRequiredMixin(AccessMixin):
    """For class-based views: officers only."""

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_officer):
            return _deny(request)
        return super().dispatch(request, *args, **kwargs)


def officer_required(view):
    """For function views: officers only."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_officer):
            return _deny(request)
        return view(request, *args, **kwargs)

    return wrapper
