from rest_framework import serializers

from .models import JobPost


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
