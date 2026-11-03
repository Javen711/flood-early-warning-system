from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from alerts.models import Alert
from monitoring.models import FloodPrediction
from residents.models import Resident
from zones.models import Zone

from .forms import normalise_phone
from .models import User


class PhoneTests(TestCase):
    def test_local_and_international_formats_are_normalised(self):
        self.assertEqual(normalise_phone('0712 345 678'), '+254712345678')
        self.assertEqual(normalise_phone('+254 712-345-678'), '+254712345678')
        self.assertEqual(normalise_phone('254712345678'), '+254712345678')

    def test_garbage_is_rejected(self):
        from django import forms
        with self.assertRaises(forms.ValidationError):
            normalise_phone('abc')


class SignUpTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(zone_name='Zone A', elevation_m=Decimal('10'))
        self.payload = {
            'full_name': 'Grace Achieng', 'phone_number': '0712345678', 'zone': self.zone.pk,
            'username': 'grace', 'password1': 'Tr0ub4dor&3xyz', 'password2': 'Tr0ub4dor&3xyz',
        }

    def test_signup_creates_resident_user_linked_record_and_logs_in(self):
        response = self.client.post(reverse('signup'), self.payload)
        self.assertRedirects(response, reverse('portal'))
        user = User.objects.get(username='grace')
        self.assertEqual(user.role, User.Role.RESIDENT)
        resident = Resident.objects.get(user=user)
        self.assertEqual((resident.zone, resident.phone_number), (self.zone, '+254712345678'))
        self.assertEqual(self.client.get(reverse('portal')).status_code, 200)

    def test_signup_cannot_choose_a_role(self):
        self.client.post(reverse('signup'), {**self.payload, 'role': 'ADMIN', 'is_superuser': 'on'})
        user = User.objects.get(username='grace')
        self.assertEqual(user.role, User.Role.RESIDENT)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_officer)

    def test_signup_links_to_resident_an_officer_already_added(self):
        existing = Resident.objects.create(full_name='Grace A.', phone_number='+254712345678', zone=self.zone)
        self.client.post(reverse('signup'), self.payload)
        self.assertEqual(Resident.objects.count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.user.username, 'grace')
        self.assertEqual(existing.full_name, 'Grace A.')  # officer's record is not overwritten

    def test_mismatched_passwords_show_an_error_and_create_nothing(self):
        response = self.client.post(reverse('signup'), {**self.payload, 'password2': 'different'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='grace').exists())

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user('grace', password='x')
        response = self.client.post(reverse('signup'), self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Resident.objects.count(), 0)


class AccessControlTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(zone_name='Zone A', elevation_m=Decimal('10'))
        self.other = Zone.objects.create(zone_name='Zone B', elevation_m=Decimal('10'))
        self.officer = User.objects.create_user('officer', password='pw12345!x', role=User.Role.OFFICER)
        self.resident_user = User.objects.create_user('res', password='pw12345!x', role=User.Role.RESIDENT)
        Resident.objects.create(full_name='Res One', phone_number='+254700000001', zone=self.zone, user=self.resident_user)

    def test_resident_is_blocked_from_every_officer_screen(self):
        self.client.login(username='res', password='pw12345!x')
        for name in ['zone-list', 'zone-add', 'resident-list', 'resident-add', 'reading-list', 'reading-add']:
            response = self.client.get(reverse(name))
            self.assertRedirects(response, reverse('portal'), msg_prefix=name, fetch_redirect_response=False)
        for name, args in [('run-prediction', [self.zone.pk]), ('run-predictions-all', []), ('fetch-weather', [])]:
            response = self.client.post(reverse(name, args=args))
            self.assertRedirects(response, reverse('portal'), msg_prefix=name, fetch_redirect_response=False)
        self.assertEqual(FloodPrediction.objects.count(), 0)

    def test_resident_hitting_dashboard_goes_to_portal(self):
        self.client.login(username='res', password='pw12345!x')
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('portal'))

    def test_officer_keeps_full_access_and_portal_sends_them_to_dashboard(self):
        self.client.login(username='officer', password='pw12345!x')
        for name in ['dashboard', 'zone-list', 'resident-list', 'reading-list']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertRedirects(self.client.get(reverse('portal')), reverse('dashboard'))

    def test_superuser_without_role_change_still_counts_as_officer(self):
        User.objects.create_superuser('root', password='pw12345!x', role=User.Role.RESIDENT)
        self.client.login(username='root', password='pw12345!x')
        self.assertEqual(self.client.get(reverse('zone-list')).status_code, 200)

    def test_anonymous_users_are_sent_to_login(self):
        for name in ['dashboard', 'portal', 'zone-list']:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)

    def test_login_lands_each_role_on_its_own_page(self):
        r = self.client.post(reverse('login'), {'username': 'res', 'password': 'pw12345!x'})
        self.assertRedirects(r, reverse('portal'))
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'officer', 'password': 'pw12345!x'})
        self.assertRedirects(r, reverse('dashboard'))


class PortalContentTests(TestCase):
    def test_resident_sees_only_their_own_zones_risk_and_alerts(self):
        zone_a = Zone.objects.create(zone_name='Zone A', elevation_m=Decimal('10'))
        zone_b = Zone.objects.create(zone_name='Zone B', elevation_m=Decimal('10'))
        for zone, level, text in [(zone_a, 'HIGH', 'Alert text for A'), (zone_b, 'MEDIUM', 'Alert text for B')]:
            prediction = FloodPrediction.objects.create(zone=zone, risk_level=level, confidence_score=0.9, model_version='t')
            Alert.objects.create(prediction=prediction, message=text)
        user = User.objects.create_user('res', password='pw12345!x', role=User.Role.RESIDENT)
        Resident.objects.create(full_name='Res', phone_number='+254700000001', zone=zone_a, user=user)

        self.client.login(username='res', password='pw12345!x')
        response = self.client.get(reverse('portal'))
        self.assertContains(response, 'Zone A')
        self.assertContains(response, 'Alert text for A')
        self.assertContains(response, 'High')
        self.assertNotContains(response, 'Alert text for B')

    def test_portal_handles_a_resident_record_that_was_deleted(self):
        user = User.objects.create_user('res', password='pw12345!x', role=User.Role.RESIDENT)
        self.client.login(username='res', password='pw12345!x')
        self.assertContains(self.client.get(reverse('portal')), 'no longer linked')
