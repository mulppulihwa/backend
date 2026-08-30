from datetime import timedelta

from django.contrib import admin
from django.db.models import CharField, Count, F, Func, Value
from django.db.models.functions import TruncDate
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from .models import RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'method', 'path', 'status_code', 'user']
    list_filter = ['method', 'status_code']
    search_fields = ['path']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    change_list_template = 'admin/analytics/requestlog/change_list.html'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_urls(self):
        custom = [
            path('summary/', self.admin_site.admin_view(self.summary_view), name='analytics_requestlog_summary'),
        ]
        return custom + super().get_urls()

    def summary_view(self, request):
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        qs_week = RequestLog.objects.filter(created_at__gte=week_ago)

        # 경로에 들어간 숫자 id를 {id}로 뭉개서 "엔드포인트 종류"별로 집계
        # 예: /api/places/169/endorse/ , /api/places/171/endorse/ -> /api/places/{id}/endorse/
        normalized_path = Func(
            F('path'), Value(r'/[0-9]+/'), Value('/{id}/'), Value('g'),
            function='regexp_replace', output_field=CharField(),
        )

        context = {
            **self.admin_site.each_context(request),
            'title': 'API 트래픽 요약',
            'total': RequestLog.objects.count(),
            'today_count': RequestLog.objects.filter(created_at__date=today).count(),
            'week_count': qs_week.count(),
            'unique_users_total': RequestLog.objects.exclude(user__isnull=True)
                .values('user').distinct().count(),
            'unique_users_week': qs_week.exclude(user__isnull=True)
                .values('user').distinct().count(),
            # 어디에(구체적인 리소스 단위) — 최근 7일간 가장 많이 조회/호출된 정확한 경로
            'top_paths': qs_week.values('path').annotate(count=Count('id')).order_by('-count')[:10],
            # 어디에(엔드포인트 종류 단위) — id를 뭉갠 패턴별 집계
            'top_actions': qs_week.annotate(action=normalized_path)
                .values('action').annotate(count=Count('id')).order_by('-count')[:10],
            # 얼마나 — 최근 14일 일별 추이
            'daily': RequestLog.objects.filter(created_at__gte=now - timedelta(days=14))
                .annotate(day=TruncDate('created_at'))
                .values('day').annotate(count=Count('id')).order_by('-day'),
        }
        return TemplateResponse(request, 'admin/analytics/requestlog/summary.html', context)
