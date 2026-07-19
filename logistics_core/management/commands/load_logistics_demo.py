import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# Core
from core.models import Organization

# CRM & Store
from crm.models import Customer
from generic_store_mgmt.models import Product, Category, UnitOfMeasure
from inventory.models import Warehouse
from hrms.models import Employee

# Logistics Core
from logistics_core.models import Zone, Location, Route, ServiceType

# WMS 3PL
from wms_3pl.models import (
    WarehouseZone, Aisle, Rack, Bin, 
    ClientInventory, PutawayTask, PickList, PickListItem
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Loads robust demo data for Logistics Core and WMS 3PL modules'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting to generate logistics demo data..."))
        
        org = Organization.objects.first()
        if not org:
            org = Organization.objects.create(
                name="Global Logistics Corp", 
                owner_name='Admin', email='admin@globallogistics.com'
            )
        
        # User & Employee
        user, _ = User.objects.get_or_create(username='warehouse_worker', defaults={'email': 'worker@glc.com'})
        if not user.password:
            user.set_password('password123')
            user.save()
            
        employee, _ = Employee.objects.get_or_create(
            user=user, 
            defaults={'employee_id': 'WH-001', 'department': 'Warehouse Operations'}
        )
        
        # 2. Master Data (Client & Product)
        client, _ = Customer.objects.get_or_create(name="Acme Electronics Ltd.")
        
        cat, _ = Category.objects.get_or_create(name="Consumer Electronics")
        uom_pcs, _ = UnitOfMeasure.objects.get_or_create(name="Pieces", defaults={'code': 'PCS'})
        uom_kg, _ = UnitOfMeasure.objects.get_or_create(name="Kilograms", defaults={'code': 'KG'})
        
        product1, _ = Product.objects.get_or_create(
            sku="LAP-PRO-15", 
            defaults={'name': 'Pro Laptop 15-inch', 'category': cat, 'uom': uom_pcs, 'selling_price': Decimal("1299.00")}
        )
        product2, _ = Product.objects.get_or_create(
            sku="MON-4K-27", 
            defaults={'name': '4K Monitor 27-inch', 'category': cat, 'uom': uom_pcs, 'selling_price': Decimal("399.00")}
        )

        # 3. Logistics Core Setup (Topology)
        zone_na, _ = Zone.objects.get_or_create(name="North America", defaults={'code': 'NA'})
        zone_eu, _ = Zone.objects.get_or_create(name="Europe", defaults={'code': 'EU'})
        
        loc_lax, _ = Location.objects.get_or_create(
            code="LAX-HUB", 
            defaults={'name': 'Los Angeles Gateway', 'location_type': 'HUB', 'zone': zone_na, 'city': 'Los Angeles'}
        )
        loc_jfk, _ = Location.objects.get_or_create(
            code="JFK-HUB", 
            defaults={'name': 'New York Central', 'location_type': 'HUB', 'zone': zone_na, 'city': 'New York'}
        )
        loc_lhr, _ = Location.objects.get_or_create(
            code="LHR-PORT", 
            defaults={'name': 'London Heathrow Port', 'location_type': 'AIRPORT', 'zone': zone_eu, 'city': 'London'}
        )
        
        # Routes
        Route.objects.get_or_create(origin=loc_lax, destination=loc_jfk, defaults={'distance_km': 3940.00, 'estimated_hours': 41.0})
        Route.objects.get_or_create(origin=loc_jfk, destination=loc_lhr, defaults={'distance_km': 5540.00, 'estimated_hours': 8.0})
        
        # Service Types
        ServiceType.objects.get_or_create(name="Next Day Air", defaults={'code': 'NDA', 'guaranteed_hours': 24})
        ServiceType.objects.get_or_create(name="Standard Ground", defaults={'code': 'STD-G', 'guaranteed_hours': 120})

        # 4. WMS 3PL Setup (Warehouse Internals)
        warehouse, _ = Warehouse.objects.get_or_create(name="LAX Mega Facility")
        
        w_zone_recv, _ = WarehouseZone.objects.get_or_create(warehouse=warehouse, name="Receiving Bay", defaults={'zone_type': 'RECEIVING'})
        w_zone_stor, _ = WarehouseZone.objects.get_or_create(warehouse=warehouse, name="Main Storage", defaults={'zone_type': 'STORAGE'})
        
        # Generate some topology
        aisle1, _ = Aisle.objects.get_or_create(zone=w_zone_stor, code="A1")
        rack1, _ = Rack.objects.get_or_create(aisle=aisle1, code="R1")
        rack2, _ = Rack.objects.get_or_create(aisle=aisle1, code="R2")
        
        bin_a1r1b1, _ = Bin.objects.get_or_create(rack=rack1, code="B1", defaults={'max_weight_kg': 500, 'max_volume_m3': 2.0})
        bin_a1r1b2, _ = Bin.objects.get_or_create(rack=rack1, code="B2", defaults={'max_weight_kg': 500, 'max_volume_m3': 2.0})
        bin_a1r2b1, _ = Bin.objects.get_or_create(rack=rack2, code="B1", defaults={'max_weight_kg': 1000, 'max_volume_m3': 5.0})

        # 5. Inventory & Tasks
        # Client Inventory Setup
        inv1, _ = ClientInventory.objects.get_or_create(
            client=client, product=product1, bin_location=bin_a1r1b1,
            defaults={'quantity': 150}
        )
        inv2, _ = ClientInventory.objects.get_or_create(
            client=client, product=product2, bin_location=bin_a1r2b1,
            defaults={'quantity': 500}
        )
        
        # Putaway Task (Pending)
        putaway, _ = PutawayTask.objects.get_or_create(
            task_number="PA-26-0001",
            defaults={
                'client': client,
                'product': product1,
                'quantity': 50,
                'target_bin': bin_a1r1b2,
                'status': 'Assigned',
                'assigned_to': employee
            }
        )
        
        # PickList (In Progress)
        picklist, _ = PickList.objects.get_or_create(
            picklist_number="PL-26-0001",
            defaults={
                'client': client,
                'assigned_to': employee,
                'order_reference': 'SO-99234',
                'status': 'Picking'
            }
        )
        
        PickListItem.objects.get_or_create(
            picklist=picklist, product=product1, source_bin=bin_a1r1b1,
            defaults={'quantity_to_pick': 10, 'quantity_picked': 4}
        )
        PickListItem.objects.get_or_create(
            picklist=picklist, product=product2, source_bin=bin_a1r2b1,
            defaults={'quantity_to_pick': 25, 'quantity_picked': 0}
        )

        self.stdout.write(self.style.SUCCESS("Successfully loaded Logistics Core & WMS 3PL demo data!"))
