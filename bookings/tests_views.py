import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Organization
from .models import BusinessProfile, IndustryPreset, ResourceType, Resource, Customer, OperatingSchedule
from django.utils import timezone

User = get_user_model()

class BookingViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', password='password')
        self.org = Organization.objects.create(
            name="Test Org",
            owner_name="Test Owner",
            email="test@example.com"
        )
        self.preset = IndustryPreset.objects.create(slug='generic', name='Generic', config={'slot_mode': 'time_slot'})
        self.business = BusinessProfile.objects.create(
            organization=self.org,
            industry=self.preset,
            name="Test Business",
            is_active=True
        )
        
        # We need a way for the middleware to assign this user to the business.
        # But wait, the standard get_business relies on `request.tenant` which is set by middleware.
        # The test client might need X-Tenant-ID header.
        self.headers = {'HTTP_X_TENANT_ID': str(self.business.id)}
        
        self.resource_type = ResourceType.objects.create(
            business=self.business,
            name="Room",
            default_capacity=2
        )
        self.resource = Resource.objects.create(
            business=self.business,
            resource_type=self.resource_type,
            name="Room 1",
            code="R1",
            capacity=2
        )
        
    def test_dashboard_view(self):
        self.client.login(username='testadmin', password='password')
        response = self.client.get(reverse('bookings:dashboard'), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")
        
    def test_calendar_view(self):
        self.client.login(username='testadmin', password='password')
        response = self.client.get(reverse('bookings:calendar'), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room 1")

    def test_public_checkout_view_get(self):
        # Public checkout requires resource_id and date
        target_date = timezone.now().date() + datetime.timedelta(days=1)
        url = reverse('bookings:public_checkout')
        
        response = self.client.get(
            url, 
            {'resource_id': self.resource.id, 'date': target_date.strftime('%Y-%m-%d'), 'selected_slot': '10:00'},
            **self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Complete Your Booking")

    def test_public_checkout_view_post_success(self):
        target_date = timezone.now().date() + datetime.timedelta(days=1)
        url = reverse('bookings:public_checkout')
        
        post_data = {
            'resource_id': self.resource.id,
            'date': target_date.strftime('%Y-%m-%d'),
            'selected_slot': '10:00',
            'name': 'Alice Bob',
            'email': 'alice@example.com',
            'phone': '1234567890'
        }
        
        response = self.client.post(url, post_data, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Booking Confirmed!")
        
        # Verify customer was created
        self.assertTrue(Customer.objects.filter(email='alice@example.com').exists())
