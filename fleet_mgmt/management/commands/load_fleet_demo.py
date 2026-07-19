import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from core.models import Organization
from hrms.models import Employee
from fleet_mgmt.models import Vehicle, Container, MaintenanceLog, DriverAssignment

User = get_user_model()

class Command(BaseCommand):
    help = 'Loads robust demo data for the Fleet Management module'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting to generate Fleet Management demo data..."))
        
        # 1. Base Setup
        org = Organization.objects.first()
        if not org:
            org = Organization.objects.create(name="Global Logistics Corp", owner_name="Admin", email="admin@glc.com")
            
        # 2. Employees (Drivers & Mechanics)
        # Driver 1
        user_d1, _ = User.objects.get_or_create(username='michael_driver', defaults={'email': 'michael@glc.com'})
        driver1, _ = Employee.objects.get_or_create(user=user_d1, defaults={'employee_id': 'DRV-010', 'department': 'Transport'})
        
        # Driver 2
        user_d2, _ = User.objects.get_or_create(username='sarah_driver', defaults={'email': 'sarah@glc.com'})
        driver2, _ = Employee.objects.get_or_create(user=user_d2, defaults={'employee_id': 'DRV-011', 'department': 'Transport'})

        # 3. Vehicles
        truck1, _ = Vehicle.objects.get_or_create(
            registration_number="TRK-1001",
            defaults={
                'vehicle_type': 'TRUCK',
                'make': 'Volvo',
                'model': 'VNL 860',
                'capacity_kg': Decimal('20000.00'),
                'volume_m3': Decimal('85.00'),
                'status': 'Available'
            }
        )
        
        van1, _ = Vehicle.objects.get_or_create(
            registration_number="VAN-2005",
            defaults={
                'vehicle_type': 'VAN',
                'make': 'Mercedes-Benz',
                'model': 'Sprinter',
                'capacity_kg': Decimal('1500.00'),
                'volume_m3': Decimal('14.00'),
                'status': 'Dispatched'
            }
        )
        
        # 4. Containers
        Container.objects.get_or_create(
            container_number="MSCU-1234567",
            defaults={'container_type': 'TEU', 'is_active': True}
        )
        Container.objects.get_or_create(
            container_number="MAEU-9876543",
            defaults={'container_type': 'FEU', 'is_active': True}
        )
        Container.objects.get_or_create(
            container_number="CMAU-COLD111",
            defaults={'container_type': 'REEFER', 'is_active': True}
        )

        # 5. Driver Assignments
        now = timezone.now()
        
        # Active assignment
        DriverAssignment.objects.get_or_create(
            vehicle=van1,
            driver=driver2,
            defaults={
                'assigned_from': now - timedelta(days=2),
                'assigned_until': None,
                'is_active': True
            }
        )
        
        # Past assignment
        DriverAssignment.objects.get_or_create(
            vehicle=truck1,
            driver=driver1,
            defaults={
                'assigned_from': now - timedelta(days=30),
                'assigned_until': now - timedelta(days=5),
                'is_active': False
            }
        )

        # 6. Maintenance Logs
        MaintenanceLog.objects.get_or_create(
            vehicle=truck1,
            description="Routine oil change and brake inspection.",
            defaults={
                'cost': Decimal('450.00'),
                'performed_by': 'Internal Workshop Team A'
            }
        )
        
        MaintenanceLog.objects.get_or_create(
            vehicle=van1,
            description="Replaced sliding door mechanism.",
            defaults={
                'cost': Decimal('210.00'),
                'performed_by': 'External Vendor - City Motors'
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully loaded Fleet Management demo data!"))
