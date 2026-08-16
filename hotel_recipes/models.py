from django.db import models
from core.mixins import AuditableMixin
from hotel_pos.models import MenuItem

class Recipe(AuditableMixin):
    menu_item = models.OneToOneField(MenuItem, on_delete=models.CASCADE, related_name='recipe')
    instructions = models.TextField(blank=True, null=True)
    prep_time_minutes = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Recipe for {self.menu_item.name}"

class RecipeVersion(AuditableMixin):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class RecipeItem(AuditableMixin):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    # Using string reference to avoid direct dependency, assuming inventory app exists
    inventory_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=50) # e.g., kg, grams, liters

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.inventory_item.name}"
