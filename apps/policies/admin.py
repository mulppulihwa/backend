from django.contrib import admin

from .models import Policy


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'managing_org', 'apply_end_date', 'is_active', 'source']
    list_filter = ['is_active', 'benefit_type', 'source']
    search_fields = ['title', 'summary', 'managing_org']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
