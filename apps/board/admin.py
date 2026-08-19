from django.contrib import admin

from .models import HousingPhoto, HousingPost, JobApplication, JobPost


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


class HousingPhotoInline(admin.TabularInline):
    model = HousingPhoto
    extra = 0
    fields = ['image', 'order']


@admin.register(HousingPost)
class HousingPostAdmin(admin.ModelAdmin):
    inlines = [HousingPhotoInline]
    list_display = ['title', 'room_type', 'region', 'deal_type', 'created_by', 'is_active']
    list_filter = ['room_type', 'region', 'deal_type', 'is_active']
    search_fields = ['title', 'detail_address']
