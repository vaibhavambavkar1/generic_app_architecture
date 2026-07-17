from django.contrib import admin
from .models import (
    IndustryPreset, BusinessProfile, ResourceType, Resource,
    OperatingSchedule, Holiday, SlotOverride, Customer,
    Booking, BookingItem, Addon, BookingAddon, PricingRule, TaxRule, Review, Waitlist
)


# ==========================================
# Inlines
# ==========================================

class ResourceTypeInline(admin.TabularInline):
    model = ResourceType
    extra = 0
    show_change_link = True

class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 0
    show_change_link = True

class OperatingScheduleInline(admin.TabularInline):
    model = OperatingSchedule
    extra = 0

class SlotOverrideInline(admin.TabularInline):
    model = SlotOverride
    extra = 0

class AddonInline(admin.TabularInline):
    model = Addon
    extra = 0
    show_change_link = True

class PricingRuleInline(admin.TabularInline):
    model = PricingRule
    extra = 0

class TaxRuleInline(admin.TabularInline):
    model = TaxRule
    extra = 0

class HolidayInline(admin.TabularInline):
    model = Holiday
    extra = 0

class CustomerInline(admin.TabularInline):
    model = Customer
    extra = 0
    show_change_link = True

class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0

class BookingAddonInline(admin.TabularInline):
    model = BookingAddon
    extra = 0

class ReviewInline(admin.StackedInline):
    model = Review
    extra = 0

class WaitlistInline(admin.TabularInline):
    model = Waitlist
    extra = 0

class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    show_change_link = True
    readonly_fields = ('booking_number', 'status', 'start_datetime', 'end_datetime', 'total_amount')
    fields = ('booking_number', 'status', 'start_datetime', 'end_datetime', 'total_amount')


# ==========================================
# Model Admins
# ==========================================

@admin.register(IndustryPreset)
class IndustryPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    search_fields = ('name', 'slug')


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'industry', 'timezone', 'currency', 'is_active')
    list_filter = ('industry', 'is_active', 'organization')
    search_fields = ('name',)
    inlines = [ResourceTypeInline, AddonInline, TaxRuleInline, HolidayInline, CustomerInline]


@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'default_capacity', 'default_duration_minutes', 'is_active')
    list_filter = ('business', 'is_active')
    search_fields = ('name',)
    inlines = [ResourceInline, PricingRuleInline]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'resource_type', 'business', 'capacity', 'is_active')
    list_filter = ('business', 'resource_type', 'is_active')
    search_fields = ('name', 'code')
    inlines = [OperatingScheduleInline, SlotOverrideInline, WaitlistInline]


@admin.register(OperatingSchedule)
class OperatingScheduleAdmin(admin.ModelAdmin):
    list_display = ('business', 'resource', 'day_of_week', 'start_time', 'end_time', 'slot_duration_minutes', 'is_active')
    list_filter = ('business', 'day_of_week', 'is_active')
    ordering = ('business', 'day_of_week', 'start_time')


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('business', 'date', 'reason')
    list_filter = ('business', 'date')
    search_fields = ('reason',)


@admin.register(SlotOverride)
class SlotOverrideAdmin(admin.ModelAdmin):
    list_display = ('business', 'resource', 'date', 'start_time', 'end_time', 'override_type')
    list_filter = ('business', 'date', 'override_type')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'business', 'user')
    list_filter = ('business',)
    search_fields = ('name', 'phone', 'email')
    inlines = [BookingInline, WaitlistInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'business', 'customer', 'status', 'slot_mode', 'start_datetime', 'end_datetime', 'total_amount')
    list_filter = ('business', 'status', 'slot_mode', 'start_datetime')
    search_fields = ('booking_number', 'customer__name', 'customer__phone')
    inlines = [BookingItemInline, BookingAddonInline, ReviewInline]
    readonly_fields = ('booking_number', 'subtotal', 'tax_amount', 'discount_amount', 'total_amount')


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'business', 'is_active')
    list_filter = ('business', 'is_active')
    search_fields = ('name',)


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('resource_type', 'business', 'pricing_model', 'base_price', 'peak_multiplier', 'weekend_multiplier', 'valid_from', 'valid_to')
    list_filter = ('business', 'pricing_model', 'valid_from')


@admin.register(TaxRule)
class TaxRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'is_inclusive', 'business')
    list_filter = ('business', 'is_inclusive')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'comment')
    list_filter = ('rating',)


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ('business', 'resource', 'customer', 'target_date')
    list_filter = ('business', 'target_date', 'resource')
    search_fields = ('customer__name', 'customer__phone', 'resource__name')
