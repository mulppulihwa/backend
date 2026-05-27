from rest_framework import serializers

from .models import User, UserPolicy, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    nickname = serializers.ReadOnlyField()
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


class UserPolicySerializer(serializers.ModelSerializer):
    policy_id    = serializers.IntegerField(source='policy.id', read_only=True)
    policy_title = serializers.CharField(source='policy.title', read_only=True)
    amount_text  = serializers.CharField(source='policy.amount_text', read_only=True)
    benefit_type = serializers.CharField(source='policy.benefit_type', read_only=True)
    apply_end_date = serializers.DateField(source='policy.apply_end_date', read_only=True)

    class Meta:
        model = UserPolicy
        fields = [
            'id', 'policy_id', 'policy_title',
            'amount_text', 'benefit_type', 'apply_end_date',
            'status', 'created_at',
        ]
