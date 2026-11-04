from rest_framework import serializers

from alerts.models import Alert, Feedback
from monitoring.models import FloodPrediction
from zones.models import Zone

RISK_ADVICE = {
    'HIGH': "Move valuables and your family to higher ground now, and follow instructions from local authorities.",
    'MEDIUM': "Stay alert. Keep your phone charged and be ready to move if the water rises.",
    'LOW': "No action needed right now. Alerts will be sent here if this changes.",
}


class ZoneChoiceSerializer(serializers.ModelSerializer):
    """Just enough to fill the 'choose your zone' list on the sign-up screen."""

    class Meta:
        model = Zone
        fields = ['id', 'zone_name', 'ward']


class RiskSerializer(serializers.ModelSerializer):
    level = serializers.CharField(source='risk_level')
    label = serializers.CharField(source='get_risk_level_display')
    confidence = serializers.FloatField(source='confidence_score')
    advice = serializers.SerializerMethodField()

    class Meta:
        model = FloodPrediction
        fields = ['level', 'label', 'confidence', 'advice', 'predicted_at']

    def get_advice(self, obj):
        return RISK_ADVICE.get(obj.risk_level, '')


class AlertSerializer(serializers.ModelSerializer):
    risk_level = serializers.CharField(source='prediction.risk_level')
    risk_label = serializers.CharField(source='prediction.get_risk_level_display')
    feedback_rating = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = ['id', 'message', 'risk_level', 'risk_label', 'sent_at', 'feedback_rating']

    def get_feedback_rating(self, obj):
        resident = self.context.get('resident')
        if resident is None:
            return None
        entry = Feedback.objects.filter(resident=resident, alert=obj).first()
        return entry.rating if entry else None


class FeedbackSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)
