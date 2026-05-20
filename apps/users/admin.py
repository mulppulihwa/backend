from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['kakao_id', 'nickname', 'profile_completed', 'date_joined']
    list_filter = ['profile_completed']
    search_fields = ['kakao_id', 'nickname']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('kakao_id', 'nickname', 'phone', 'profile_completed')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('날짜', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('kakao_id', 'nickname', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'region_code', 'gender', 'income_level', 'is_farm_registered']
    list_filter = ['gender', 'income_level', 'is_farm_registered']
    search_fields = ['user__kakao_id', 'user__nickname', 'region_code']
    raw_id_fields = ['user']
