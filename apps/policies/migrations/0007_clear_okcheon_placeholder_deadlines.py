from datetime import date

from django.db import migrations

# 마이그레이션 0006 적용 전 수동입력했던 '연말까지' placeholder 값
# (옥천군 농어촌 기본소득 시범사업 pk=17만 시범사업 기간상 2027-12-31)
PLACEHOLDER_END_DATES = {17: date(2027, 12, 31)}
DEFAULT_PLACEHOLDER_END_DATE = date(2026, 12, 31)


def clear_placeholder_deadlines(apps, schema_editor):
    Policy = apps.get_model('policies', 'Policy')
    Policy.objects.filter(source='옥천군청').update(apply_end_date=None)


def restore_placeholder_deadlines(apps, schema_editor):
    Policy = apps.get_model('policies', 'Policy')
    for policy in Policy.objects.filter(source='옥천군청'):
        policy.apply_end_date = PLACEHOLDER_END_DATES.get(policy.pk, DEFAULT_PLACEHOLDER_END_DATE)
        policy.save(update_fields=['apply_end_date'])


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0006_manual_source_to_okcheon'),
    ]

    operations = [
        migrations.RunPython(clear_placeholder_deadlines, restore_placeholder_deadlines),
    ]
