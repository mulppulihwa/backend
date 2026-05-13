from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models

BENEFIT_TYPES = [
    ('현금지원', '현금지원'), ('교육', '교육'), ('컨설팅', '컨설팅'),
    ('시설', '시설'), ('세금감면', '세금감면'), ('현물', '현물'), ('기타', '기타'),
]
SOURCES = [
    ('복지로', '복지로'), ('수동입력', '수동입력'), ('귀농센터', '귀농센터'),
]


class Policy(models.Model):
    title         = models.CharField(max_length=200)
    summary       = models.TextField()
    description   = models.TextField(blank=True)
    benefit_type  = models.CharField(max_length=20, choices=BENEFIT_TYPES, blank=True)
    amount        = models.IntegerField(null=True, blank=True)
    amount_text   = models.CharField(max_length=100, blank=True)
    source        = models.CharField(max_length=20, choices=SOURCES, default='수동입력')

    # 1차 SQL 필터 조건
    min_age        = models.SmallIntegerField(default=0)
    max_age        = models.SmallIntegerField(default=130)
    gender         = models.CharField(max_length=10, default='all')
    region_codes   = ArrayField(models.TextField(), default=list)
    occupation_tags = ArrayField(models.TextField(), default=list)
    household_type = ArrayField(models.TextField(), default=list)
    move_status    = ArrayField(models.TextField(), default=list)
    income_level   = ArrayField(models.TextField(), default=list)
    disability_required = models.BooleanField(null=True)  # None=무관, True=장애인만

    # 복합 조건 트리
    condition_tree = models.JSONField(null=True, blank=True)

    # 신청 정보
    apply_start_date = models.DateField(null=True, blank=True)
    apply_end_date   = models.DateField(null=True, blank=True)
    apply_url        = models.URLField(blank=True)
    managing_org     = models.CharField(max_length=100, blank=True)
    source_url       = models.URLField(blank=True)
    external_id      = models.CharField(max_length=100, blank=True)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'policies'
        indexes = [
            models.Index(fields=['min_age', 'max_age']),
            models.Index(fields=['apply_end_date']),
            GinIndex(fields=['region_codes'],     name='idx_policies_region_codes'),
            GinIndex(fields=['occupation_tags'],  name='idx_policies_occupation_tags'),
            GinIndex(fields=['income_level'],     name='idx_policies_income_level'),
        ]
