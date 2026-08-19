from django.contrib import admin

from .models import JobApplication, JobPost


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ['applicant', 'name', 'phone', 'applied_at']
    readonly_fields = ['applied_at']


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    inlines = [JobApplicationInline]
    list_display = ['title', 'category', 'region', 'created_by', 'is_active']
    list_filter = ['category', 'region', 'is_active']
    search_fields = ['title', 'description']
