from django.contrib import admin
from .models import Vehicle, Container, MaintenanceLog, DriverAssignment

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'vehicle_type', 'capacity_kg', 'status')
    list_filter = ('vehicle_type', 'status')
    search_fields = ('registration_number', 'make', 'model')

@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ('container_number', 'container_type', 'is_active')
    list_filter = ('container_type', 'is_active')
    search_fields = ('container_number',)

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date_logged', 'cost', 'performed_by')
    search_fields = ('vehicle__registration_number', 'description')

@admin.register(DriverAssignment)
class DriverAssignmentAdmin(admin.ModelAdmin):
    list_display = ('driver', 'vehicle', 'assigned_from', 'assigned_until', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('driver__user__first_name', 'driver__user__last_name', 'vehicle__registration_number')
