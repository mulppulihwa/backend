import logging

from .models import RequestLog

logger = logging.getLogger(__name__)

EXCLUDED_PREFIXES = ('/admin/', '/static/', '/api/docs/', '/api/schema/')


class RequestLogMiddleware:
    """API 호출 수 기준 트래픽 집계용 요청 로깅 (다른 팀원은 /admin/에서 확인)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.path.startswith(EXCLUDED_PREFIXES):
            try:
                RequestLog.objects.create(
                    path=request.path[:255],
                    method=request.method,
                    status_code=response.status_code,
                    user=request.user if request.user.is_authenticated else None,
                )
            except Exception as e:
                logger.warning('요청 로그 저장 실패 (무시): %s', e)

        return response
