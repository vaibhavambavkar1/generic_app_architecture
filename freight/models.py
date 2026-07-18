from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition
from crm.models import Customer
from logistics_core.models import Zone, Location, ServiceType
from fleet_mgmt.models import Container
from inventory.models import Supplier

class FreightBooking(WorkflowMixin):
    booking_number = models.CharField(max_length=50, unique=True)
    shipper = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='freight_shipped')
    consignee = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='freight_received')
    
    origin_port = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='freight_origin')
    destination_port = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='freight_destination')
    
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True)
    
    weight_kg = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    volume_m3 = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    
    # States: Quoted -> Booked -> Received -> Customs Pending -> Loaded -> In Transit -> Arrived -> Cleared -> Delivered
    @transition(field='status', source='Draft', target='Quoted')
    def quote(self): pass
    @transition(field='status', source='Quoted', target='Booked')
    def book(self): pass
    @transition(field='status', source='Booked', target='Received')
    def receive(self): pass
    @transition(field='status', source='Received', target='Customs Pending')
    def customs_pending(self): pass
    @transition(field='status', source=['Customs Pending', 'Received'], target='Loaded')
    def load(self): pass
    @transition(field='status', source='Loaded', target='In Transit')
    def transit(self): pass
    @transition(field='status', source='In Transit', target='Arrived')
    def arrive(self): pass
    @transition(field='status', source='Arrived', target='Cleared')
    def clear_customs(self): pass
    @transition(field='status', source='Cleared', target='Delivered')
    def deliver(self): pass

    def __str__(self):
        return f"Freight {self.booking_number}"

class BillOfLading(AuditableMixin):
    booking = models.OneToOneField(FreightBooking, on_delete=models.CASCADE, related_name='bol')
    bol_number = models.CharField(max_length=100, unique=True)
    vessel_name = models.CharField(max_length=100)
    voyage_number = models.CharField(max_length=50)
    containers = models.ManyToManyField(Container, related_name='bols', blank=True)
    issue_date = models.DateField(auto_now_add=True)
    
class AirWaybill(AuditableMixin):
    booking = models.OneToOneField(FreightBooking, on_delete=models.CASCADE, related_name='awb')
    awb_number = models.CharField(max_length=100, unique=True)
    flight_number = models.CharField(max_length=50)
    departure_airport = models.CharField(max_length=100)
    destination_airport = models.CharField(max_length=100)
    issue_date = models.DateField(auto_now_add=True)

class CustomsDeclaration(WorkflowMixin):
    booking = models.OneToOneField(FreightBooking, on_delete=models.CASCADE, related_name='customs')
    declaration_number = models.CharField(max_length=100, unique=True, blank=True)
    customs_agent = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    duty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    @transition(field='status', source='Draft', target='Submitted')
    def submit(self): pass
    @transition(field='status', source='Submitted', target='Cleared')
    def clear(self): pass
    @transition(field='status', source='Submitted', target='Rejected')
    def reject(self): pass

class FreightLeg(AuditableMixin):
    booking = models.ForeignKey(FreightBooking, on_delete=models.CASCADE, related_name='legs')
    sequence = models.IntegerField(default=1)
    origin = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='leg_origins')
    destination = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='leg_destinations')
    carrier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    mode_of_transport = models.CharField(max_length=50, choices=[('ROAD', 'Road'), ('RAIL', 'Rail'), ('SEA', 'Sea'), ('AIR', 'Air')])
    
    class Meta:
        ordering = ['sequence']
