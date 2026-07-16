from django.contrib import admin
from .models import Category, Brand, UnitOfMeasure, TaxBracket, Product, PriceList, PriceListItem

class SubcategoryInline(admin.TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 1

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1
    fields = ('name', 'sku', 'uom', 'product_type', 'is_active')
    show_change_link = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [SubcategoryInline, ProductInline]

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [ProductInline]

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    inlines = [ProductInline]

@admin.register(TaxBracket)
class TaxBracketAdmin(admin.ModelAdmin):
    list_display = ('name', 'cgst_rate', 'sgst_rate', 'igst_rate', 'total_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [ProductInline]

class PriceListItemInline(admin.TabularInline):
    model = PriceListItem
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'product_type', 'category', 'brand', 'manage_stock', 'is_active')
    list_filter = ('product_type', 'is_active', 'manage_stock', 'category', 'brand')
    search_fields = ('name', 'sku', 'barcode')
    readonly_fields = ('sku',)
    inlines = [PriceListItemInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'barcode', 'product_type', 'is_active')
        }),
        ('Classification', {
            'fields': ('category', 'brand', 'uom', 'tax_bracket')
        }),
        ('Pricing', {
            'fields': ('purchase_price', 'selling_price', 'mrp')
        }),
        ('Inventory', {
            'fields': ('manage_stock',)
        }),
    )

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [PriceListItemInline]
