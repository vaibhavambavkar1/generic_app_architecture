from django.contrib import admin
from .models import FreightBooking, BillOfLading, AirWaybill, CustomsDeclaration, FreightLeg

class FreightLegInline(admin.TabularInline):
    model = FreightLeg
    extra = 1

@admin.register(FreightBooking)
class FreightBookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'shipper', 'consignee', 'status', 'service_type')
    list_filter = ('status', 'service_type')
    search_fields = ('booking_number', 'shipper__name', 'consignee__name')
    inlines = [FreightLegInline]

@admin.register(BillOfLading)
class BillOfLadingAdmin(admin.ModelAdmin):
    list_display = ('bol_number', 'booking', 'vessel_name', 'voyage_number', 'issue_date')
    search_fields = ('bol_number', 'vessel_name', 'booking__booking_number')

@admin.register(AirWaybill)
class AirWaybillAdmin(admin.ModelAdmin):
    list_display = ('awb_number', 'booking', 'flight_number', 'issue_date')
    search_fields = ('awb_number', 'flight_number', 'booking__booking_number')

@admin.register(CustomsDeclaration)
class CustomsDeclarationAdmin(admin.ModelAdmin):
    list_display = ('declaration_number', 'booking', 'status', 'duty_amount')
    list_filter = ('status',)
    search_fields = ('declaration_number', 'booking__booking_number')
