from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition
from crm.models import Customer
from logistics_core.models import Zone, ServiceType, Route
from fleet_mgmt.models import Vehicle
from hrms.models import Employee

class Waybill(WorkflowMixin):
    waybill_number = models.CharField(max_length=50, unique=True)
    
    sender = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_waybills')
    sender_address = models.TextField(blank=True)
    
    receiver_name = models.CharField(max_length=200)
    receiver_phone = models.CharField(max_length=20)
    receiver_address = models.TextField()
    
    origin_zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name='origin_waybills')
    destination_zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name='destination_waybills')
    
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    volume_m3 = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True)
    chargeable_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        
        # Calculate chargeable weight (e.g., standard volumetric factor 1 m3 = 200 kg)
        if self.volume_m3:
            vol_weight = self.volume_m3 * Decimal('200.0')
            self.chargeable_weight = max(self.weight_kg, vol_weight)
        else:
            self.chargeable_weight = self.weight_kg

        # Simple pricing logic based on chargeable weight
        if self.service_type:
            base_rate = Decimal('10.0')
            per_kg_rate = Decimal('5.0')
            if 'express' in self.service_type.name.lower():
                base_rate = Decimal('25.0')
                per_kg_rate = Decimal('8.0')
            self.price = base_rate + (self.chargeable_weight * per_kg_rate)
            
        super().save(*args, **kwargs)
    
    @transition(field='status', source='Draft', target='Manifested')
    def add_to_manifest(self):
        pass

    @transition(field='status', source='Manifested', target='At Hub')
    def receive_at_hub(self):
        pass

    @transition(field='status', source=['At Hub', 'Manifested'], target='In Transit')
    def mark_in_transit(self):
        pass

    @transition(field='status', source='In Transit', target='Out for Delivery')
    def out_for_delivery(self):
        pass

    @transition(field='status', source='Out for Delivery', target='Delivered')
    def mark_delivered(self):
        pass

    @transition(field='status', source=['Out for Delivery', 'In Transit'], target='Failed')
    def mark_failed(self):
        pass

    def __str__(self):
        return self.waybill_number


class DispatchManifest(WorkflowMixin):
    manifest_number = models.CharField(max_length=50, unique=True)
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispatch_manifests')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispatch_manifests')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    
    @transition(field='status', source='Draft', target='Dispatched')
    def dispatch(self):
        # When dispatched, update all waybills in manifest
        for item in self.items.all():
            try:
                # Assuming waybills are currently in 'At Hub' or 'Manifested'
                item.waybill.mark_in_transit()
                item.waybill.save()
            except Exception:
                pass

    @transition(field='status', source='Dispatched', target='Closed')
    def close_manifest(self):
        pass

    def __str__(self):
        return f"{self.manifest_number} - {self.date}"


class ManifestItem(AuditableMixin):
    manifest = models.ForeignKey(DispatchManifest, on_delete=models.CASCADE, related_name='items')
    waybill = models.ForeignKey(Waybill, on_delete=models.CASCADE, related_name='manifest_items')
    sequence = models.IntegerField(default=0, help_text="Delivery order sequence")

    class Meta:
        unique_together = ('manifest', 'waybill')
        ordering = ['sequence']

    def __str__(self):
        return f"{self.manifest.manifest_number} - {self.waybill.waybill_number}"


class ProofOfDelivery(AuditableMixin):
    waybill = models.OneToOneField(Waybill, on_delete=models.CASCADE, related_name='pod')
    received_by = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    signature = models.ImageField(upload_to='pods/signatures/', blank=True, null=True)
    photo = models.ImageField(upload_to='pods/photos/', blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"POD for {self.waybill.waybill_number}"
