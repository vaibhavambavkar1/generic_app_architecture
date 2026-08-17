from django.contrib import admin
from .models import Table, MenuCategory, MenuItem, CashierShift, Order, OrderItem

# Unregister periodic tasks from django_celery_beat which was loaded earlier
try:
    from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule, SolarSchedule, ClockedSchedule
    admin.site.unregister(PeriodicTask)
    admin.site.unregister(IntervalSchedule)
    admin.site.unregister(CrontabSchedule)
    admin.site.unregister(SolarSchedule)
    admin.site.unregister(ClockedSchedule)
except Exception:
    pass

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'branch', 'capacity', 'is_active')
    search_fields = ('number',)
    list_filter = ('is_active', 'branch')

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active', 'branch')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_vegetarian', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active', 'is_vegetarian', 'category')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'branch', 'table', 'customer_name', 'total_amount', 'created_at')
    list_filter = ('branch', 'created_at')
    inlines = [OrderItemInline]

@admin.register(CashierShift)
class CashierShiftAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'start_time', 'end_time', 'is_open')
    list_filter = ('is_open', 'branch', 'user')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'price')
