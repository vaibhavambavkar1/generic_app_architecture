from django.contrib import admin
from .models import Zone, Location, Route, ServiceType

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location_type', 'city', 'zone', 'is_active')
    list_filter = ('location_type', 'zone', 'is_active')
    search_fields = ('name', 'code', 'city')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'distance_km', 'estimated_hours', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('origin__name', 'destination__name')

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'guaranteed_hours', 'is_active')
    search_fields = ('name', 'code')
