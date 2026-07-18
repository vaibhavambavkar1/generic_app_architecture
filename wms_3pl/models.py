from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition
from inventory.models import Warehouse
from generic_store_mgmt.models import Product
from crm.models import Customer
from hrms.models import Employee

class WarehouseZone(AuditableMixin):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=50, choices=[
        ('RECEIVING', 'Receiving Area'),
        ('STORAGE', 'General Storage'),
        ('COLD', 'Cold Storage'),
        ('PICKING', 'Picking Zone'),
        ('PACKING', 'Packing Area'),
        ('SHIPPING', 'Shipping Dock')
    ], default='STORAGE')

    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"

class Aisle(AuditableMixin):
    zone = models.ForeignKey(WarehouseZone, on_delete=models.CASCADE, related_name='aisles')
    code = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.zone} - Aisle {self.code}"

class Rack(AuditableMixin):
    aisle = models.ForeignKey(Aisle, on_delete=models.CASCADE, related_name='racks')
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.aisle} - Rack {self.code}"

class Bin(AuditableMixin):
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name='bins')
    code = models.CharField(max_length=50)
    max_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_volume_m3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.rack} - Bin {self.code}"

class ClientInventory(AuditableMixin):
    """
    Multi-tenant inventory tracking at the bin level for 3PL operations.
    """
    client = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='inventory_records')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='client_inventory')
    bin_location = models.ForeignKey(Bin, on_delete=models.PROTECT, related_name='inventory_contents')
    quantity = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('client', 'product', 'bin_location')
        
    def __str__(self):
        return f"{self.client.name} | {self.product.name} | Qty: {self.quantity} at {self.bin_location}"

class PutawayTask(WorkflowMixin):
    """
    Task to move received goods from Receiving to a specific Storage Bin.
    """
    task_number = models.CharField(max_length=50, unique=True)
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Customer, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    target_bin = models.ForeignKey(Bin, on_delete=models.PROTECT)
    
    @transition(field='status', source='Draft', target='Assigned')
    def assign(self): pass
    
    @transition(field='status', source='Assigned', target='In Progress')
    def start_putaway(self): pass
    
    @transition(field='status', source='In Progress', target='Completed')
    def complete_putaway(self):
        # Update client inventory
        inventory, created = ClientInventory.objects.get_or_create(
            client=self.client,
            product=self.product,
            bin_location=self.target_bin,
            defaults={'quantity': 0}
        )
        inventory.quantity += self.quantity
        inventory.save()

    def __str__(self):
        return f"Putaway {self.task_number} - {self.product.name}"

class PickList(WorkflowMixin):
    """
    Instructions for picking items from bins to fulfill an order (e.g. Courier Waybill or Freight Booking).
    """
    picklist_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Customer, on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    order_reference = models.CharField(max_length=100, blank=True, help_text="e.g. Waybill or SO number")
    
    @transition(field='status', source='Draft', target='Assigned')
    def assign(self): pass
    
    @transition(field='status', source='Assigned', target='Picking')
    def start_picking(self): pass
    
    @transition(field='status', source='Picking', target='Packed')
    def pack(self): pass
    
    @transition(field='status', source='Packed', target='Shipped')
    def ship(self): pass

    def __str__(self):
        return f"PickList {self.picklist_number}"

class PickListItem(AuditableMixin):
    picklist = models.ForeignKey(PickList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    source_bin = models.ForeignKey(Bin, on_delete=models.PROTECT)
    quantity_to_pick = models.IntegerField()
    quantity_picked = models.IntegerField(default=0)
    
    def mark_picked(self, qty):
        self.quantity_picked = qty
        self.save()
        # Deduct from bin inventory
        try:
            inv = ClientInventory.objects.get(
                client=self.picklist.client,
                product=self.product,
                bin_location=self.source_bin
            )
            inv.quantity -= qty
            inv.save()
        except ClientInventory.DoesNotExist:
            pass
