from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class LocalPlace(models.Model):
    CATEGORIES = [
        ('농자재', '농자재'), ('농기계', '농기계'), ('행정', '행정'),
        ('생활', '생활'), ('명소', '명소'), ('음식점', '음식점'),
        ('동호회', '동호회'), ('부동산', '부동산'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    business_hours = models.CharField(max_length=100, blank=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    subsidy_tags = ArrayField(models.TextField(), default=list)
    receipt_claimable = models.BooleanField(default=False)
    local_memo = models.TextField(blank=True)
    price_notes = models.TextField(blank=True)
    last_verified = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # 신뢰도 기반 안심 검증 마크 — 관리자 큐레이션
    okcheon_news_recommended = models.BooleanField(default=False)
    counseling_center_recommended = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='registered_places',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'local_places'
        indexes = [
            models.Index(fields=['category']),
            GinIndex(fields=['subsidy_tags'], name='idx_places_subsidy_tags'),
        ]


class PlaceEndorsement(models.Model):
    place = models.ForeignKey(LocalPlace, on_delete=models.CASCADE, related_name='endorsements')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='place_endorsements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'place_endorsements'
        unique_together = [['place', 'user']]
