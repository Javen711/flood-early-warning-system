from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.forms import ResidentSignUpForm
from alerts.models import Alert, Feedback
from residents.models import Resident
from zones.models import Zone

from .permissions import IsResident
from .serializers import (
    AlertSerializer, FeedbackSerializer, RiskSerializer, ZoneChoiceSerializer,
)


def _resident_for(user):
    return Resident.objects.filter(user=user).select_related('zone').first()


def _user_payload(user):
    resident = _resident_for(user)
    return {
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'role': user.role,
        'phone_number': resident.phone_number if resident else user.contact_number,
        'zone': ZoneChoiceSerializer(resident.zone).data if resident else None,
    }


def _auth_response(user, http_status=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': _user_payload(user)}, status=http_status)


class ZoneListView(ListAPIView):
    """Public list of zones, so someone can pick theirs while signing up."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ZoneChoiceSerializer
    pagination_class = None
    queryset = Zone.objects.all()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'auth'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        data = dict(request.data.items())
        # The app sends one 'password'; the web form's two fields are filled from it.
        if 'password' in data:
            data.setdefault('password1', data['password'])
            data.setdefault('password2', data['password'])
        form = ResidentSignUpForm(data)
        if not form.is_valid():
            errors = {
                field: [item['message'] for item in items]
                for field, items in form.errors.get_json_data().items()
            }
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        user = form.save()
        return _auth_response(user, status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'auth'
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        user = authenticate(
            request,
            username=request.data.get('username', ''),
            password=request.data.get('password', ''),
        )
        if user is None:
            return Response(
                {'detail': "Wrong username or password."}, status=status.HTTP_400_BAD_REQUEST,
            )
        return _auth_response(user)


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(_user_payload(request.user))


class MyZoneView(APIView):
    """The app's home screen: this resident's zone, its current risk, latest alerts."""

    permission_classes = [IsResident]

    def get(self, request):
        resident = _resident_for(request.user)
        if resident is None:
            return Response({'zone': None, 'risk': None, 'alerts': []})
        zone = resident.zone
        prediction = zone.latest_prediction()
        alerts = Alert.objects.filter(prediction__zone=zone).select_related('prediction')[:5]
        return Response({
            'zone': ZoneChoiceSerializer(zone).data,
            'risk': RiskSerializer(prediction).data if prediction else None,
            'alerts': AlertSerializer(alerts, many=True, context={'resident': resident}).data,
        })


class AlertListView(ListAPIView):
    permission_classes = [IsResident]
    serializer_class = AlertSerializer

    def get_queryset(self):
        resident = _resident_for(self.request.user)
        if resident is None:
            return Alert.objects.none()
        return Alert.objects.filter(prediction__zone=resident.zone).select_related('prediction')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['resident'] = _resident_for(self.request.user)
        return context


class AlertFeedbackView(APIView):
    """A resident rates an alert they could see (1 = not useful, 5 = very useful)."""

    permission_classes = [IsResident]

    def post(self, request, alert_id):
        resident = _resident_for(request.user)
        if resident is None:
            return Response({'detail': "No resident record."}, status=status.HTTP_404_NOT_FOUND)
        alert = get_object_or_404(Alert, pk=alert_id, prediction__zone=resident.zone)
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, created = Feedback.objects.update_or_create(
            resident=resident, alert=alert,
            defaults={
                'rating': serializer.validated_data['rating'],
                'comment': serializer.validated_data.get('comment', ''),
            },
        )
        return Response(
            {'alert': alert.id, 'rating': serializer.validated_data['rating']},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
