from django.contrib import admin

from .models import LocalPlace, PlaceEndorsement


@admin.register(LocalPlace)
class LocalPlaceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'address', 'created_by', 'is_active',
        'okcheon_news_recommended', 'counseling_center_recommended',
    ]
    list_filter = ['category', 'is_active', 'receipt_claimable', 'okcheon_news_recommended', 'counseling_center_recommended']
    list_editable = ['okcheon_news_recommended', 'counseling_center_recommended']
    search_fields = ['name', 'address']


@admin.register(PlaceEndorsement)
class PlaceEndorsementAdmin(admin.ModelAdmin):
    list_display = ['place', 'user', 'created_at']
    list_filter = ['place']
