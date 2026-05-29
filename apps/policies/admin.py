from django.contrib import admin

from lib.exceptions import PolicyParseError
from lib.parsing.policy_parser import parse_policy

from .models import ChecklistItem, Policy


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1
    fields = ['order', 'label']


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    inlines = [ChecklistItemInline]
    list_display = ['title', 'managing_org', 'apply_end_date', 'is_active', 'source']
    list_filter = ['is_active', 'benefit_type', 'source']
    search_fields = ['title', 'summary', 'managing_org']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['parse_from_text']

    fieldsets = [
        ('기본 정보', {'fields': ['title', 'summary', 'description', 'benefit_type', 'amount', 'amount_text', 'source']}),
        ('자격 조건', {'fields': ['min_age', 'max_age', 'gender', 'region_codes', 'occupation_tags', 'household_type', 'move_status', 'income_level', 'disability_required', 'condition_tree']}),
        ('신청 정보', {'fields': ['apply_start_date', 'apply_end_date', 'apply_url', 'managing_org', 'source_url', 'external_id', 'is_active']}),
        ('AI 파싱', {'fields': ['raw_text'], 'description': '공고문 원문을 붙여넣고 "AI로 공고문 자동 파싱" 액션을 실행하세요.'}),
        ('메타', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]

    @admin.action(description='AI로 공고문 자동 파싱')
    def parse_from_text(self, request, queryset):
        for policy in queryset:
            if not policy.raw_text.strip():
                self.message_user(request, f'{policy.title}: 공고문 텍스트가 없습니다.', level='warning')
                continue
            try:
                result = parse_policy(policy.raw_text)
                for field, val in result['parsed'].items():
                    if hasattr(policy, field) and field not in ('confidence', 'flags'):
                        setattr(policy, field, val)
                policy.save()
                self.message_user(request, f'{policy.title}: 파싱 완료 (confidence={result["confidence"]:.2f})')
            except PolicyParseError as e:
                self.message_user(request, f'{policy.title}: {e}', level='error')
