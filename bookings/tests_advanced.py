import json
import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Organization
from .models import BusinessProfile, IndustryPreset, ResourceType, Resource, Customer, Waitlist
from .services.booking_service import BookingService

User = get_user_model()

class AdvancedSaaSTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.org = Organization.objects.create(name="Test Org")
        self.preset = IndustryPreset.objects.create(
            name="Generic", slug="generic", config={'slot_mode': 'time_slot'}
        )
        self.business = BusinessProfile.objects.create(
            organization=self.org, industry=self.preset, name="Test Business", is_active=True
        )
        
        # Set tenant header for API calls
        self.client.credentials(HTTP_X_TENANT_ID=str(self.business.id))
        
        self.customer = Customer.objects.create(
            business=self.business, name="John Doe", email="john@example.com", phone="1234567890"
        )
        self.resource_type = ResourceType.objects.create(
            business=self.business, name="Room", default_duration_minutes=60
        )
        self.resource = Resource.objects.create(
            business=self.business, resource_type=self.resource_type, name="Room 101", code="R101", capacity=1
        )
        
    def test_waitlist_creation(self):
        waitlist = Waitlist.objects.create(
            business=self.business,
            resource=self.resource,
            customer=self.customer,
            target_date=timezone.now().date()
        )
        self.assertEqual(waitlist.customer.name, "John Doe")
        self.assertFalse(waitlist.is_fulfilled)

    def test_recurring_bookings_engine(self):
        start_dt = timezone.now() + datetime.timedelta(days=1)
        end_dt = start_dt + datetime.timedelta(hours=1)
        
        bookings = BookingService.create_recurring_bookings(
            business=self.business,
            customer=self.customer,
            base_start_dt=start_dt,
            base_end_dt=end_dt,
            items=[{"resource": self.resource, "quantity": 1}],
            frequency="daily",
            count=3
        )
        self.assertEqual(len(bookings), 3)
        self.assertEqual(bookings[0].start_datetime.date(), start_dt.date())
        self.assertEqual(bookings[1].start_datetime.date(), (start_dt + datetime.timedelta(days=1)).date())
        self.assertEqual(bookings[2].start_datetime.date(), (start_dt + datetime.timedelta(days=2)).date())

    def test_api_resource_list(self):
        response = self.client.get(reverse('bookings:api-resource-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Room 101")
        
    def test_public_calendar_access(self):
        # We need a standard django test client without auth
        from django.test import Client
        public_client = Client()
        # Mocking the tenant middleware for tests usually requires passing HTTP headers 
        # but since we fall back to the first active business, it should load.
        response = public_client.get(reverse('bookings:public_booking'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Business")
