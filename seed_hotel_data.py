import os
import django
from datetime import time
from django.utils import timezone
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_framework.settings')
django.setup()

from core.models import Organization
from bookings.models import (
    IndustryPreset, BusinessProfile, ResourceType, Resource,
    OperatingSchedule, PricingRule
)

def seed():
    print("Seeding Hotel & Resort Test Data...")
    
    # 1. Organization (Singleton)
    org = Organization.objects.first()
    if not org:
        org = Organization.objects.create(
            name="Global Hospitality Corp",
            owner_name="Test Owner",
            email="hospitality@example.com",
            phone="555-0199"
        )
    
    # 2. Industry Preset
    preset = IndustryPreset.objects.get(slug="hotel-resort")
    
    # 3. Business Profile
    business, created = BusinessProfile.objects.get_or_create(
        organization=org,
        industry=preset,
        name="Test Hotel & Resort Bookings Business",
        defaults={
            "timezone": "UTC",
            "currency": "USD"
        }
    )
    if created:
        print(f"Created Business: {business.name}")
    else:
        print(f"Business already exists: {business.name}")

    # 4. Resource Type (Room Type)
    res_type, created = ResourceType.objects.get_or_create(
        business=business,
        name="Deluxe Suite",
        defaults={
            "default_capacity": 1,
            "default_duration_minutes": 60
        }
    )
    if created:
        print(f"Created Resource Type: {res_type.name}")
        
    # 5. Resource
    resource, created = Resource.objects.get_or_create(
        business=business,
        resource_type=res_type,
        code="RES-01",
        defaults={
            "name": "Deluxe Suite 01",
            "capacity": 1
        }
    )
    if created:
        print(f"Created Resource: {resource.name}")

    # 6. Operating Schedule (Available everyday 00:00 to 23:59 for a hotel, but matching README 09:00 to 18:00 for test purposes)
    for day in range(7):
        schedule, created = OperatingSchedule.objects.get_or_create(
            business=business,
            resource=resource,
            day_of_week=day,
            defaults={
                "start_time": time(9, 0),
                "end_time": time(18, 0),
                "slot_duration_minutes": None # Hotels usually book by day, so slot duration is irrelevant
            }
        )
        if created:
            print(f"Created Operating Schedule for Day {day}")

    # 7. Pricing Rule
    pricing, created = PricingRule.objects.get_or_create(
        business=business,
        resource_type=res_type,
        pricing_model="DAILY",
        defaults={
            "base_price": Decimal("150.00"),
            "valid_from": timezone.now().date()
        }
    )
    if created:
        print(f"Created Pricing Rule: {pricing.pricing_model} - ${pricing.base_price}")
        
    print("✅ Hotel & Resort test data seeded successfully!")

if __name__ == "__main__":
    seed()
