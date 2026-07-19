import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# Models
from core.models import Organization
from crm.models import Customer
from hrms.models import Employee
from logistics_core.models import Zone, Route, Location
from fleet_mgmt.models import Vehicle, DriverAssignment
from courier.models import Waybill, DispatchManifest, ManifestItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Loads demo data for Courier and Fleet Dispatch'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting to generate Courier Manifest demo data..."))
        
        org = Organization.objects.first()
        if not org:
            org = Organization.objects.create(name="Global Logistics Corp", owner_name="Admin", email="admin@glc.com")
            
        # Get/Create Driver
        user, _ = User.objects.get_or_create(username='driver_john', defaults={'email': 'john@glc.com'})
        driver, _ = Employee.objects.get_or_create(
            user=user, defaults={'employee_id': 'DRV-001', 'department': 'Transport'}
        )
        
        # Get/Create Vehicle
        vehicle, _ = Vehicle.objects.get_or_create(
            registration_number="TRK-9999", 
            defaults={'vehicle_type': 'VAN', 'make': 'Ford', 'model': 'Transit', 'capacity_kg': 1500, 'status': 'Available'}
        )
        
        # Get/Create Zones & Route
        zone_origin, _ = Zone.objects.get_or_create(name="Downtown Hub", defaults={'code': 'DT-1'})
        zone_dest, _ = Zone.objects.get_or_create(name="Suburbs Region", defaults={'code': 'SUB-1'})
        
        loc_start, _ = Location.objects.get_or_create(name="Downtown Terminal", defaults={'zone': zone_origin, 'code': 'DT-TERM'})
        loc_end, _ = Location.objects.get_or_create(name="Suburbs Delivery Point", defaults={'zone': zone_dest, 'code': 'SUB-DEL'})
        
        route, _ = Route.objects.get_or_create(
            origin=loc_start, destination=loc_end, 
            defaults={'distance_km': 45.0, 'estimated_hours': 2.0}
        )
        
        # Customers
        sender, _ = Customer.objects.get_or_create(name="E-Commerce Store Inc.")
        
        # Create Waybills
        waybills = []
        for i in range(1, 6):
            wb, _ = Waybill.objects.get_or_create(
                waybill_number=f"AWB-DEMO-{i}",
                defaults={
                    'sender': sender,
                    'receiver_name': f"Customer {i}",
                    'receiver_phone': f"555-010{i}",
                    'receiver_address': f"{i}23 Main St, Suburbs",
                    'origin_zone': zone_origin,
                    'destination_zone': zone_dest,
                    'weight_kg': Decimal("5.50"),
                    'price': Decimal("15.00"),
                    'status': 'Manifested' # Needs to be Manifested or At Hub to be put on a manifest
                }
            )
            waybills.append(wb)
            
        # Create Manifest
        manifest, created = DispatchManifest.objects.get_or_create(
            manifest_number="MAN-DEMO-26-001",
            defaults={
                'driver': driver,
                'vehicle': vehicle,
                'route': route,
                'status': 'Draft'
            }
        )
        
        if created:
            for i, wb in enumerate(waybills):
                ManifestItem.objects.create(
                    manifest=manifest,
                    waybill=wb,
                    sequence=i+1
                )
            self.stdout.write(self.style.SUCCESS("Manifest MAN-DEMO-26-001 created successfully with 5 Waybills!"))
        else:
            self.stdout.write(self.style.SUCCESS("Manifest MAN-DEMO-26-001 already exists."))
            
