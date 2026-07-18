from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition
from hrms.models import Employee

class Vehicle(WorkflowMixin):
    VEHICLE_TYPES = (
        ('TRUCK', 'Truck (FTL)'),
        ('VAN', 'Delivery Van'),
        ('BIKE', 'Motorcycle'),
        ('TRAILER', 'Trailer'),
        ('RAIL', 'Rail Wagon'),
    )
    
    registration_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    capacity_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum payload capacity in KG")
    volume_m3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Volume capacity in Cubic Meters")
    
    # States: Available -> Dispatched -> In Maintenance -> Out of Service
    @transition(field='status', source='Available', target='Dispatched')
    def dispatch(self):
        pass

    @transition(field='status', source=['Available', 'Dispatched'], target='In Maintenance')
    def send_to_maintenance(self):
        pass

    @transition(field='status', source='In Maintenance', target='Available')
    def mark_available(self):
        pass

    @transition(field='status', source='*', target='Out of Service')
    def decommission(self):
        pass

    def __str__(self):
        return f"{self.registration_number} ({self.get_vehicle_type_display()})"

class Container(AuditableMixin):
    CONTAINER_TYPES = (
        ('TEU', '20ft Container (TEU)'),
        ('FEU', '40ft Container (FEU)'),
        ('REEFER', 'Refrigerated Container'),
    )
    container_number = models.CharField(max_length=50, unique=True)
    container_type = models.CharField(max_length=20, choices=CONTAINER_TYPES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.container_number} - {self.get_container_type_display()}"

class MaintenanceLog(AuditableMixin):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_logs')
    date_logged = models.DateField(auto_now_add=True)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    performed_by = models.CharField(max_length=255, blank=True, help_text="Internal workshop or external vendor")

    def __str__(self):
        return f"Maintenance {self.vehicle.registration_number} on {self.date_logged}"

class DriverAssignment(AuditableMixin):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='driver_assignments')
    driver = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='vehicle_assignments')
    assigned_from = models.DateTimeField()
    assigned_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.driver.user.get_full_name()} -> {self.vehicle.registration_number}"
