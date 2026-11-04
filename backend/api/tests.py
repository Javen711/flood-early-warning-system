from decimal import Decimal

from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from alerts.models import Alert, Feedback
from monitoring.models import FloodPrediction
from residents.models import Resident
from zones.models import Zone

GOOD_PASSWORD = 'Tr0ub4dor&3xyz'


class ApiTestBase(APITestCase):
    def setUp(self):
        cache.clear()  # the sign-in throttle counts requests in the cache
        self.zone_a = Zone.objects.create(zone_name='Zone A', ward='Ward A', elevation_m=Decimal('10'))
        self.zone_b = Zone.objects.create(zone_name='Zone B', elevation_m=Decimal('10'))

    def make_alert(self, zone, level='HIGH', text='alert'):
        prediction = FloodPrediction.objects.create(
            zone=zone, risk_level=level, confidence_score=0.9, model_version='t',
        )
        return Alert.objects.create(prediction=prediction, message=text)

    def register(self, **overrides):
        payload = {
            'full_name': 'Grace Achieng', 'phone_number': '0712345678', 'zone': self.zone_a.pk,
            'username': 'grace', 'password': GOOD_PASSWORD,
        }
        payload.update(overrides)
        return self.client.post(reverse('api-register'), payload, format='json')

    def auth(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        return client

    def resident_client(self, username='grace'):
        response = self.register(username=username, phone_number='0712345678')
        return self.auth(response.data['token'])


class AuthApiTests(ApiTestBase):
    def test_zones_are_public_and_minimal(self):
        response = self.client.get(reverse('api-zones'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({z['zone_name'] for z in response.data}, {'Zone A', 'Zone B'})
        self.assertEqual(set(response.data[0].keys()), {'id', 'zone_name', 'ward'})

    def test_register_creates_resident_and_returns_token_and_profile(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['token'])
        self.assertEqual(response.data['user']['role'], 'RESIDENT')
        self.assertEqual(response.data['user']['phone_number'], '+254712345678')
        self.assertEqual(response.data['user']['zone']['zone_name'], 'Zone A')
        self.assertTrue(Resident.objects.filter(user__username='grace', zone=self.zone_a).exists())

    def test_register_ignores_attempts_to_choose_a_role(self):
        self.register(role='ADMIN', is_superuser=True)
        user = User.objects.get(username='grace')
        self.assertEqual(user.role, 'RESIDENT')
        self.assertFalse(user.is_superuser)

    def test_register_reports_field_errors(self):
        response = self.register(phone_number='12', password='abc')
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone_number', response.data['errors'])
        self.assertIn('password2', response.data['errors'])
        self.assertFalse(User.objects.filter(username='grace').exists())

    def test_login_logout_cycle(self):
        self.register()
        bad = self.client.post(reverse('api-login'), {'username': 'grace', 'password': 'nope'}, format='json')
        self.assertEqual(bad.status_code, 400)
        good = self.client.post(reverse('api-login'), {'username': 'grace', 'password': GOOD_PASSWORD}, format='json')
        self.assertEqual(good.status_code, 200)
        client = self.auth(good.data['token'])
        self.assertEqual(client.get(reverse('api-me')).status_code, 200)
        self.assertEqual(client.post(reverse('api-logout')).status_code, 204)
        self.assertEqual(client.get(reverse('api-me')).status_code, 401)

    def test_protected_endpoints_reject_anonymous_callers(self):
        for name in ['api-me', 'api-my-zone', 'api-alerts']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 401, name)

    def test_sign_in_is_throttled(self):
        for _ in range(30):
            self.client.post(reverse('api-login'), {'username': 'x', 'password': 'y'}, format='json')
        response = self.client.post(reverse('api-login'), {'username': 'x', 'password': 'y'}, format='json')
        self.assertEqual(response.status_code, 429)


class ResidentApiTests(ApiTestBase):
    def test_my_zone_shows_only_the_residents_zone(self):
        self.make_alert(self.zone_a, 'HIGH', 'Message for A')
        self.make_alert(self.zone_b, 'MEDIUM', 'Message for B')
        client = self.resident_client()
        data = client.get(reverse('api-my-zone')).data
        self.assertEqual(data['zone']['zone_name'], 'Zone A')
        self.assertEqual(data['risk']['level'], 'HIGH')
        self.assertIn('higher ground', data['risk']['advice'])
        self.assertEqual([a['message'] for a in data['alerts']], ['Message for A'])

    def test_my_zone_without_a_prediction_has_no_risk(self):
        data = self.resident_client().get(reverse('api-my-zone')).data
        self.assertIsNone(data['risk'])
        self.assertEqual(data['alerts'], [])

    def test_alert_list_is_paginated_and_isolated(self):
        for i in range(25):
            self.make_alert(self.zone_a, 'MEDIUM', f'A{i}')
        self.make_alert(self.zone_b, 'HIGH', 'Other zone')
        data = self.resident_client().get(reverse('api-alerts')).data
        self.assertEqual(data['count'], 25)
        self.assertEqual(len(data['results']), 20)
        self.assertNotIn('Other zone', [a['message'] for a in data['results']])

    def test_feedback_is_saved_updated_and_shown_back(self):
        alert = self.make_alert(self.zone_a)
        client = self.resident_client()
        url = reverse('api-alert-feedback', args=[alert.pk])
        self.assertEqual(client.post(url, {'rating': 4, 'comment': 'Helpful'}, format='json').status_code, 201)
        self.assertEqual(client.post(url, {'rating': 2}, format='json').status_code, 200)
        self.assertEqual(Feedback.objects.filter(alert=alert).count(), 1)
        self.assertEqual(Feedback.objects.get(alert=alert).rating, 2)
        self.assertEqual(client.get(reverse('api-alerts')).data['results'][0]['feedback_rating'], 2)

    def test_feedback_rating_must_be_1_to_5(self):
        alert = self.make_alert(self.zone_a)
        client = self.resident_client()
        for bad in (0, 6, 'x'):
            response = client.post(reverse('api-alert-feedback', args=[alert.pk]), {'rating': bad}, format='json')
            self.assertEqual(response.status_code, 400, bad)

    def test_feedback_on_another_zones_alert_is_not_found(self):
        other = self.make_alert(self.zone_b)
        client = self.resident_client()
        response = client.post(reverse('api-alert-feedback', args=[other.pk]), {'rating': 3}, format='json')
        self.assertEqual(response.status_code, 404)

    def test_officer_cannot_use_resident_endpoints(self):
        User.objects.create_user('officer', password=GOOD_PASSWORD, role=User.Role.OFFICER)
        token = self.client.post(
            reverse('api-login'), {'username': 'officer', 'password': GOOD_PASSWORD}, format='json',
        ).data['token']
        client = self.auth(token)
        self.assertEqual(client.get(reverse('api-me')).status_code, 200)
        self.assertEqual(client.get(reverse('api-my-zone')).status_code, 403)
        self.assertEqual(client.get(reverse('api-alerts')).status_code, 403)

    def test_health_check_still_works(self):
        self.assertEqual(self.client.get('/api/health/').status_code, 200)
