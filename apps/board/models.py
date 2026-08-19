from django.db import models

OKCHEON_REGIONS = [
    ('옥천읍', '옥천읍'), ('동이면', '동이면'), ('안남면', '안남면'), ('청성면', '청성면'),
    ('청산면', '청산면'), ('이원면', '이원면'), ('군서면', '군서면'), ('군북면', '군북면'),
]

JOB_CATEGORIES = [
    ('농촌일손', '농촌일손'), ('주택수리', '주택수리'), ('돌봄', '돌봄'), ('동아리', '동아리'), ('기타', '기타'),
]


class JobPost(models.Model):
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=JOB_CATEGORIES)
    region = models.CharField(max_length=10, choices=OKCHEON_REGIONS, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    recruit_count = models.IntegerField(null=True, blank=True)
    conditions = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='job_posts',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_posts'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['region']),
        ]


class JobApplication(models.Model):
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='job_applications')
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_applications'
        unique_together = [['job_post', 'applicant']]
