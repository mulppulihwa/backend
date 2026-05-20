from rest_framework import serializers

from .models import LocalPlace


class LocalPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalPlace
        fields = [
            'id', 'name', 'category', 'address', 'phone',
            'lat', 'lng', 'subsidy_tags', 'receipt_claimable',
        ]
