from django.contrib import admin

from .models import LocalPlace


@admin.register(LocalPlace)
class LocalPlaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'address', 'created_by', 'is_active']
    list_filter = ['category', 'is_active', 'receipt_claimable']
    search_fields = ['name', 'address']
