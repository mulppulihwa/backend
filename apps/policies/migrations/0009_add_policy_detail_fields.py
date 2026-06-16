from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0008_clear_far_future_deadlines'),
    ]

    operations = [
        migrations.AddField(
            model_name='policy',
            name='qualification_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='policy',
            name='how_to_apply',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='policy',
            name='apply_institution',
            field=models.CharField(max_length=200, blank=True),
        ),
    ]
