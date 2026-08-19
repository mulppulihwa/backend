from rest_framework import serializers

from .models import HousingPhoto, HousingPost, JobApplication, JobPost


class JobPostSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    created_by_nickname = serializers.CharField(source='created_by.nickname', read_only=True)

    class Meta:
        model = JobPost
        fields = [
            'id', 'title', 'category', 'region', 'description', 'location',
            'start_date', 'end_date', 'recruit_count', 'conditions',
            'created_by', 'created_by_nickname', 'is_owner', 'created_at',
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.created_by_id == user.id


class JobPostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = [
            'title', 'category', 'region', 'description', 'location',
            'start_date', 'end_date', 'recruit_count', 'conditions',
        ]
        extra_kwargs = {
            'region': {'required': False},
            'location': {'required': False},
            'start_date': {'required': False},
            'end_date': {'required': False},
            'recruit_count': {'required': False},
            'conditions': {'required': False},
        }


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'name', 'phone', 'message', 'applied_at']


class HousingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingPhoto
        fields = ['id', 'image', 'order']


class HousingPostSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()
    photos = HousingPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = HousingPost
        fields = [
            'id', 'title', 'region', 'detail_address', 'room_type', 'room_layout',
            'size_pyeong', 'deal_type', 'deposit', 'monthly_rent', 'maintenance_fee',
            'options', 'description', 'contact_name', 'contact_phone', 'lat', 'lng',
            'photos', 'is_owner', 'created_at',
        ]

    def get_is_owner(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.created_by_id == user.id


class HousingPostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingPost
        fields = [
            'title', 'region', 'detail_address', 'room_type', 'room_layout',
            'size_pyeong', 'deal_type', 'deposit', 'monthly_rent', 'maintenance_fee',
            'options', 'description', 'contact_name', 'contact_phone',
        ]
        extra_kwargs = {
            'region': {'required': False},
            'room_layout': {'required': False},
            'size_pyeong': {'required': False},
            'deposit': {'required': False},
            'monthly_rent': {'required': False},
            'maintenance_fee': {'required': False},
            'options': {'required': False},
            'description': {'required': False},
        }
