from django.db import models
from core.mixins import AuditableMixin

class Zone(AuditableMixin):
    """
    Geographical zone used for routing, pricing, and dispatching.
    """
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'North Region', 'Downtown'")
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Location(AuditableMixin):
    """
    Physical location across the logistics network. Can be a hub, customer address, port, etc.
    """
    LOCATION_TYPES = (
        ('HUB', 'Logistics Hub / Terminal'),
        ('PORT', 'Sea Port'),
        ('AIRPORT', 'Airport'),
        ('RAIL', 'Railway Station'),
        ('CUSTOMER', 'Customer Location'),
        ('BORDER', 'Border Crossing'),
        ('OTHER', 'Other'),
    )
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, blank=True, help_text="UN/LOCODE or internal code")
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default='HUB')
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name='locations')
    
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city} ({self.get_location_type_display()})"

class Route(AuditableMixin):
    """
    Defined path between two hubs/locations with estimated transit times.
    """
    origin = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='routes_origin')
    destination = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='routes_destination')
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Estimated transit time in hours")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('origin', 'destination')

    def __str__(self):
        return f"{self.origin.name} -> {self.destination.name}"

class ServiceType(AuditableMixin):
    """
    Types of logistics services offered (e.g., Next Day Delivery, Standard Freight, Cold Chain).
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    guaranteed_hours = models.IntegerField(null=True, blank=True, help_text="SLA for delivery in hours")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
