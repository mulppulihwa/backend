from datetime import date

from django.db import migrations

# lib/parsing/policy_parser.MAX_VALID_END_YEAR과 동일한 기준
MAX_VALID_END_YEAR = 2030


def clear_far_future_deadlines(apps, schema_editor):
    Policy = apps.get_model('policies', 'Policy')
    Policy.objects.filter(apply_end_date__gte=date(MAX_VALID_END_YEAR, 1, 1)).update(apply_end_date=None)


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0007_clear_okcheon_placeholder_deadlines'),
    ]

    operations = [
        migrations.RunPython(clear_far_future_deadlines, migrations.RunPython.noop),
    ]
