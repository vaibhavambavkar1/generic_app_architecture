import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.models import Organization
from crm.models import Customer
from inventory.models import Supplier
from logistics_core.models import Location, Zone, ServiceType
from fleet_mgmt.models import Container
from freight.models import FreightBooking, BillOfLading, CustomsDeclaration, FreightLeg

User = get_user_model()

class Command(BaseCommand):
    help = 'Loads robust demo data for Freight Forwarding & Multimodal module'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting to generate Freight demo data..."))
        
        # 1. Base Setup
        org = Organization.objects.first()
        if not org:
            org = Organization.objects.create(name="Global Logistics Corp", owner_name="Admin", email="admin@glc.com")
            
        # 2. Master Data
        shipper, _ = Customer.objects.get_or_create(name="Global Tech Manufacturers")
        consignee, _ = Customer.objects.get_or_create(name="European Retail Distributions Ltd")
        
        customs_agent, _ = Supplier.objects.get_or_create(name="Apex Customs Brokerage")
        ocean_carrier, _ = Supplier.objects.get_or_create(name="Maersk Line")
        road_carrier, _ = Supplier.objects.get_or_create(name="EuroTruck Logistics")

        # Zones & Locations
        zone_cn, _ = Zone.objects.get_or_create(name="China Coast", defaults={'code': 'CN-C'})
        zone_eu, _ = Zone.objects.get_or_create(name="Western Europe", defaults={'code': 'WE-EU'})
        
        loc_shenzhen, _ = Location.objects.get_or_create(
            code="SZX-PORT", defaults={'name': 'Port of Shenzhen', 'location_type': 'SEAPORT', 'zone': zone_cn, 'city': 'Shenzhen'}
        )
        loc_rotterdam, _ = Location.objects.get_or_create(
            code="RTM-PORT", defaults={'name': 'Port of Rotterdam', 'location_type': 'SEAPORT', 'zone': zone_eu, 'city': 'Rotterdam'}
        )
        loc_berlin, _ = Location.objects.get_or_create(
            code="BER-HUB", defaults={'name': 'Berlin Central Hub', 'location_type': 'HUB', 'zone': zone_eu, 'city': 'Berlin'}
        )
        
        service_ocean, _ = ServiceType.objects.get_or_create(name="Ocean FCL Standard", defaults={'code': 'OC-FCL'})

        # Container
        container1, _ = Container.objects.get_or_create(container_number="MSCU-9988776", defaults={'container_type': 'FEU'})

        # 3. Create Freight Booking
        booking, created = FreightBooking.objects.get_or_create(
            booking_number="FRT-2026-9001",
            defaults={
                'shipper': shipper,
                'consignee': consignee,
                'origin_port': loc_shenzhen,
                'destination_port': loc_berlin,
                'service_type': service_ocean,
                'weight_kg': Decimal('18500.00'),
                'volume_m3': Decimal('65.00'),
                'status': 'In Transit'
            }
        )
        
        if created:
            # Document 1: Bill of Lading (Ocean)
            bol, _ = BillOfLading.objects.get_or_create(
                booking=booking,
                bol_number="BOL-MAEU-4455",
                defaults={
                    'vessel_name': 'MSC Daniela',
                    'voyage_number': '093W'
                }
            )
            bol.containers.add(container1)
            
            # Document 2: Customs Declaration
            CustomsDeclaration.objects.get_or_create(
                booking=booking,
                defaults={
                    'declaration_number': 'CUS-NL-2026-88',
                    'customs_agent': customs_agent,
                    'duty_amount': Decimal('4500.00'),
                    'status': 'Cleared'
                }
            )
            
            # Multimodal Legs
            # Leg 1: Sea Freight (Shenzhen to Rotterdam)
            FreightLeg.objects.create(
                booking=booking,
                sequence=1,
                origin=loc_shenzhen,
                destination=loc_rotterdam,
                carrier=ocean_carrier,
                mode_of_transport='SEA'
            )
            
            # Leg 2: Road Freight (Rotterdam to Berlin)
            FreightLeg.objects.create(
                booking=booking,
                sequence=2,
                origin=loc_rotterdam,
                destination=loc_berlin,
                carrier=road_carrier,
                mode_of_transport='ROAD'
            )
            
            self.stdout.write(self.style.SUCCESS("Successfully created Multimodal Freight Booking FRT-2026-9001!"))
        else:
            self.stdout.write(self.style.SUCCESS("Freight Booking FRT-2026-9001 already exists."))
