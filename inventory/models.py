from django.db import models
from core.models import WorkflowMixin

class Item(models.Model):
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    stock_quantity = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"

class PurchaseOrder(WorkflowMixin, models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"PO for {self.quantity} x {self.item.name}"
