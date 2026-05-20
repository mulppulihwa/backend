from rest_framework import serializers

from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    years_since_move = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        exclude = ['user']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['kakao_id', 'nickname', 'phone', 'profile_completed', 'profile']
