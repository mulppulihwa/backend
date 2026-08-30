from django.db import models


class RequestLog(models.Model):
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.SmallIntegerField()
    user = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='request_logs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'request_logs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['path']),
        ]
