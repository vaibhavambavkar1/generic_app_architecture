from django.contrib import admin
from .models import HotelBranch

@admin.register(HotelBranch)
class HotelBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'organization')
    search_fields = ('name', 'code')
    list_filter = ('is_active', 'organization')
