from django.db import models
from core.models import WorkflowMixin

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Item(WorkflowMixin, models.Model):
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Stock caching & thresholds
    stock_quantity = models.IntegerField(default=0, help_text="Cached global stock total")
    minimum_stock_level = models.IntegerField(default=10)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"

class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=50, help_text="e.g., Aisle 1, Bin A")
    
    class Meta:
        unique_together = ('warehouse', 'name')

    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"

class StockLevel(models.Model):
    """Cache table representing current stock of an item in a specific warehouse/location."""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_levels')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_levels')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('item', 'warehouse', 'location')

    def __str__(self):
        loc = f" ({self.location.name})" if self.location else ""
        return f"{self.item.name} at {self.warehouse.name}{loc}: {self.quantity}"

class StockLedger(models.Model):
    """Append-only immutable ledger for all inventory movements."""
    TRANSACTION_TYPES = (
        ('IN_PO', 'Purchase Order Receipt'),
        ('OUT_SO', 'Sales Order Dispatch'),
        ('ADJ', 'Manual Adjustment'),
        ('TRANS', 'Warehouse Transfer'),
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='ledger_entries')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='ledger_entries')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity_change = models.IntegerField(help_text="Positive for IN, Negative for OUT")
    reference_document = models.CharField(max_length=100, help_text="e.g., PO-1024 or ADJ-99")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} | {self.item.sku} | {'+' if self.quantity_change > 0 else ''}{self.quantity_change} | {self.created_at.date()}"

class Vendor(WorkflowMixin, models.Model):
    name = models.CharField(max_length=100)
    contact_email = models.EmailField(blank=True)
    
    def __str__(self):
        return self.name

class PurchaseOrder(WorkflowMixin, models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders', null=True)
    po_number = models.CharField(max_length=50, unique=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # We keep a reference to a specific warehouse where these goods will be received
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True)
    
    def __str__(self):
        return self.po_number or f"PO #{self.id}"

class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.item.name} for {self.po}"
