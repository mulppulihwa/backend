from rest_framework import serializers

from .models import LocalPlace


class LocalPlaceSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = LocalPlace
        fields = [
            'id', 'name', 'category', 'address', 'phone', 'business_hours',
            'local_memo', 'lat', 'lng', 'subsidy_tags', 'receipt_claimable',
            'is_owner',
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.created_by_id == user.id


class LocalPlaceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalPlace
        fields = ['name', 'category', 'address', 'phone', 'business_hours', 'local_memo', 'lat', 'lng']
        extra_kwargs = {
            'phone': {'required': False},
            'business_hours': {'required': False},
            'local_memo': {'required': False},
            'lat': {'required': False},
            'lng': {'required': False},
        }
