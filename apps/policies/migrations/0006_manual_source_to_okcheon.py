from django.db import migrations


def manual_to_okcheon(apps, schema_editor):
    Policy = apps.get_model('policies', 'Policy')
    Policy.objects.filter(source='수동입력').update(source='옥천군청')


def okcheon_to_manual(apps, schema_editor):
    Policy = apps.get_model('policies', 'Policy')
    Policy.objects.filter(source='옥천군청').update(source='수동입력')


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0005_alter_policy_source'),
    ]

    operations = [
        migrations.RunPython(manual_to_okcheon, okcheon_to_manual),
    ]
