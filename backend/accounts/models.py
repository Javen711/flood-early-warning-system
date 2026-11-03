from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    The USER entity from the ER diagram, built on top of Django's built-in
    auth system rather than reinventing password hashing/sessions ourselves.

    AbstractUser already gives us: username, password (hashed), email,
    first_name, last_name, is_staff, is_superuser, last_login, etc.
    We only add the two fields the ER diagram calls for that Django doesn't
    already provide: role and contact_number.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'System Administrator'
        OFFICER = 'OFFICER', 'Disaster Management Officer'
        RESIDENT = 'RESIDENT', 'Resident'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OFFICER,
        help_text="Controls what this user can see and do on the dashboard.",
    )
    contact_number = models.CharField(max_length=20, blank=True)

    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_resident(self):
        return self.role == self.Role.RESIDENT

    @property
    def is_officer(self):
        """Admins, officers and superusers can use the officer dashboard and
        management screens. Residents cannot."""
        return self.is_superuser or self.role in (self.Role.ADMIN, self.Role.OFFICER)

    def __str__(self):
        return self.get_full_name() or self.username
