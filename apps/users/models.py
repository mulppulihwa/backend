from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

GENDER_CHOICES    = [('남', '남'), ('여', '여')]
MARITAL_CHOICES   = [('미혼', '미혼'), ('기혼', '기혼')]
HOUSEHOLD_CHOICES = [('독거', '독거'), ('부부', '부부'), ('기타', '기타')]
INCOME_CHOICES    = [('기초수급', '기초수급'), ('차상위', '차상위'), ('일반', '일반')]


class UserManager(BaseUserManager):
    def create_user(self, kakao_id, password=None, **extra_fields):
        user = self.model(kakao_id=kakao_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, kakao_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(kakao_id, password, **extra_fields)


class User(AbstractUser):
    username = None
    kakao_id = models.TextField(unique=True)
    objects = UserManager()
    nickname = models.TextField(blank=True)
    phone    = models.TextField(blank=True)

    profile_completed = models.BooleanField(default=False)

    USERNAME_FIELD  = 'kakao_id'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # 기본 정보
    region_code = models.TextField(blank=True)
    birth_date  = models.DateField(null=True, blank=True)
    gender      = models.CharField(max_length=5, choices=GENDER_CHOICES, blank=True)

    # 귀농/귀촌 상태
    occupation_tags = ArrayField(models.TextField(), default=list, blank=True)
    move_in_date    = models.DateField(null=True, blank=True)

    # 경제 상태
    household_type  = models.CharField(max_length=10, choices=HOUSEHOLD_CHOICES, blank=True)
    income_level    = models.CharField(max_length=10, choices=INCOME_CHOICES, blank=True)
    non_farm_income = models.IntegerField(null=True, blank=True)  # 만원 단위
    marital_status  = models.CharField(max_length=5, choices=MARITAL_CHOICES, blank=True)

    # 농업 자격
    is_farm_registered   = models.BooleanField(null=True)
    farm_registered_date = models.DateField(null=True, blank=True)
    education_hours      = models.SmallIntegerField(default=0)

    # 복지로 API 매칭용
    is_disabled = models.BooleanField(null=True)  # 장애 여부

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def years_since_move(self):
        if not self.move_in_date:
            return None
        return (timezone.now().date() - self.move_in_date).days / 365

    class Meta:
        db_table = 'user_profiles'


class UserPolicy(models.Model):
    class Status(models.TextChoices):
        PENDING        = '신청예정'
        APPLIED        = '신청완료'
        NOT_INTERESTED = '관심없음'

    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_policies')
    policy  = models.ForeignKey('policies.Policy', on_delete=models.CASCADE)
    status  = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    d7_alerted_at = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'user_policies'
        unique_together = [['profile', 'policy']]
