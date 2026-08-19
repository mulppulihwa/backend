from rest_framework import serializers

from .models import LocalPlace


class LocalPlaceSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    endorsement_count = serializers.SerializerMethodField()
    is_endorsed = serializers.SerializerMethodField()

    class Meta:
        model = LocalPlace
        fields = [
            'id', 'name', 'category', 'address', 'phone', 'business_hours',
            'local_memo', 'lat', 'lng', 'subsidy_tags', 'receipt_claimable',
            'is_owner', 'okcheon_news_recommended', 'counseling_center_recommended',
            'endorsement_count', 'is_endorsed',
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.created_by_id == user.id

    def get_endorsement_count(self, obj):
        count = getattr(obj, 'endorsement_count_anno', None)
        return count if count is not None else obj.endorsements.count()

    def get_is_endorsed(self, obj):
        anno = getattr(obj, 'is_endorsed_anno', None)
        if anno is not None:
            return anno
        user = self.context['request'].user
        return user.is_authenticated and obj.endorsements.filter(user=user).exists()


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
