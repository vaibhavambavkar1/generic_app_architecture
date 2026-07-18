from django.test import TestCase
from django.db import IntegrityError
from logistics_core.models import Zone, Location, Route, ServiceType
from core.models import Organization

class LogisticsCoreTests(TestCase):
    def setUp(self):
        # Create foundational organization data
        Organization.objects.create(name="Test Org", owner_name="Owner", email="test@org.com")
        
        # Set up Zone
        self.zone = Zone.objects.create(
            name="North America",
            code="NA",
            description="North American Continent"
        )
        
        # Set up Locations
        self.location_origin = Location.objects.create(
            name="Los Angeles Hub",
            code="LAX-01",
            location_type="HUB",
            zone=self.zone,
            city="Los Angeles",
            country="USA"
        )
        self.location_destination = Location.objects.create(
            name="New York Hub",
            code="JFK-01",
            location_type="HUB",
            zone=self.zone,
            city="New York",
            country="USA"
        )
        
        # Set up Route
        self.route = Route.objects.create(
            origin=self.location_origin,
            destination=self.location_destination,
            distance_km=4500.50,
            estimated_hours=48.0
        )
        
        # Set up ServiceType
        self.service_type = ServiceType.objects.create(
            name="Express Overnight",
            code="EXP-ON",
            guaranteed_hours=24
        )

    def test_zone_creation(self):
        """Test Zone model attributes and string representation."""
        self.assertEqual(self.zone.name, "North America")
        self.assertEqual(self.zone.code, "NA")
        self.assertTrue(self.zone.is_active)
        self.assertEqual(str(self.zone), "North America (NA)")

    def test_location_creation(self):
        """Test Location model attributes, relationship with Zone, and string representation."""
        self.assertEqual(self.location_origin.name, "Los Angeles Hub")
        self.assertEqual(self.location_origin.code, "LAX-01")
        self.assertEqual(self.location_origin.zone, self.zone)
        self.assertEqual(self.location_origin.get_location_type_display(), "Logistics Hub / Terminal")
        self.assertEqual(str(self.location_origin), "Los Angeles Hub - Los Angeles (Logistics Hub / Terminal)")

    def test_route_creation(self):
        """Test Route model creation and string representation."""
        self.assertEqual(self.route.origin, self.location_origin)
        self.assertEqual(self.route.destination, self.location_destination)
        self.assertEqual(self.route.distance_km, 4500.50)
        self.assertEqual(self.route.estimated_hours, 48.0)
        self.assertEqual(str(self.route), "Los Angeles Hub -> New York Hub")

    def test_route_unique_together(self):
        """Test that the origin and destination pair is unique in the Route model."""
        with self.assertRaises(IntegrityError):
            Route.objects.create(
                origin=self.location_origin,
                destination=self.location_destination,
                distance_km=100.0,
                estimated_hours=2.0
            )

    def test_service_type_creation(self):
        """Test ServiceType model creation."""
        self.assertEqual(self.service_type.name, "Express Overnight")
        self.assertEqual(self.service_type.code, "EXP-ON")
        self.assertEqual(self.service_type.guaranteed_hours, 24)
        self.assertTrue(self.service_type.is_active)
        self.assertEqual(str(self.service_type), "Express Overnight")
