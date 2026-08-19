from django.contrib import admin

from .models import JobPost


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'region', 'created_by', 'is_active']
    list_filter = ['category', 'region', 'is_active']
    search_fields = ['title', 'description']
