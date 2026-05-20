from django.db import models


class Region(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=50)
    parent_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'regions'

    def __str__(self):
        return f'{self.name} ({self.code})'
