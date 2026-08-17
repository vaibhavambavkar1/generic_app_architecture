from django.contrib import admin
from .models import Recipe, RecipeVersion, RecipeItem

class RecipeItemInline(admin.TabularInline):
    model = RecipeItem
    extra = 1

class RecipeVersionInline(admin.TabularInline):
    model = RecipeVersion
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'prep_time_minutes', 'is_active')
    search_fields = ('menu_item__name',)
    list_filter = ('is_active',)
    inlines = [RecipeItemInline, RecipeVersionInline]

@admin.register(RecipeItem)
class RecipeItemAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'inventory_item', 'quantity', 'unit')
    search_fields = ('recipe__menu_item__name', 'inventory_item__name')

@admin.register(RecipeVersion)
class RecipeVersionAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'version_number', 'cost', 'created_at')
