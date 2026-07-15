from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from hrms.models import Employee
from django_fsm import transition

class AssetCategory(AuditableMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Asset(WorkflowMixin):
    """
    IT Asset Tracking using WorkflowMixin for lifecycle states:
    Available -> In Use -> Under Maintenance -> Retired
    """
    name = models.CharField(max_length=200)
    category = models.ForeignKey(AssetCategory, on_delete=models.RESTRICT, related_name='assets')
    serial_number = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True)
    
    purchase_date = models.DateField(blank=True, null=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    warranty_expiry = models.DateField(blank=True, null=True)
    
    current_assignee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')

    @transition(field='status', source=['Available', 'Under Maintenance'], target='In Use')
    def assign_asset(self, employee):
        """Assign asset to an employee."""
        self.current_assignee = employee

    @transition(field='status', source='In Use', target='Available')
    def return_asset(self):
        """Asset returned by employee."""
        self.current_assignee = None

    @transition(field='status', source='*', target='Under Maintenance')
    def send_to_maintenance(self):
        """Asset sent for repairs."""
        pass

    @transition(field='status', source='*', target='Retired')
    def retire_asset(self):
        """Asset reached end of life."""
        self.current_assignee = None

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = f"AST-{self.serial_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.barcode})"


class AssetAssignment(AuditableMixin):
    """
    History of asset assignments.
    """
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignment_history')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='asset_history')
    assigned_date = models.DateField(auto_now_add=True)
    returned_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset.name} to {self.employee.user.get_full_name()}"


class MaintenanceRecord(AuditableMixin):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField()
    performed_by = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Maintenance on {self.asset.name} - {self.date}"
