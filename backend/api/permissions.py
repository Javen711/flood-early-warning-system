from rest_framework.permissions import BasePermission


class IsResident(BasePermission):
    """Only self-registered residents may use the resident endpoints."""

    message = "This is only available to resident accounts."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_resident)
