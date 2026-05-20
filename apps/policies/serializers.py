from rest_framework import serializers

from .models import Policy


class PolicyCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'summary', 'amount_text',
            'benefit_type', 'apply_end_date', 'managing_org',
        ]


class PolicyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'summary', 'description',
            'benefit_type', 'amount', 'amount_text',
            'apply_start_date', 'apply_end_date', 'apply_url',
            'managing_org', 'source_url', 'source',
        ]
