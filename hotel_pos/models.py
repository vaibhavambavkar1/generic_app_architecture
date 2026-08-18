from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from hotel_core.models import HotelBranch
from django.conf import settings

class Table(AuditableMixin):
    branch = models.ForeignKey(HotelBranch, on_delete=models.CASCADE, related_name='tables')
    number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.branch.code} - Table {self.number}"

class MenuCategory(AuditableMixin):
    branch = models.ForeignKey(HotelBranch, on_delete=models.CASCADE, related_name='menu_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.branch.code})"

class MenuItem(AuditableMixin):
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_vegetarian = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class CashierShift(AuditableMixin):
    branch = models.ForeignKey(HotelBranch, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_open = models.BooleanField(default=True)

class TaxConfiguration(AuditableMixin):
    branch = models.ForeignKey(HotelBranch, on_delete=models.CASCADE, related_name='taxes')
    name = models.CharField(max_length=50, help_text="e.g., GST, VAT")
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.percentage}%) - {self.branch.code}"

class Order(WorkflowMixin):
    branch = models.ForeignKey(HotelBranch, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    shift = models.ForeignKey(CashierShift, on_delete=models.SET_NULL, null=True, blank=True)
    waiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='waiter_orders')
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_tax_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def subtotal(self):
        return self.total_amount - self.tax_amount

class OrderItem(WorkflowMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price
