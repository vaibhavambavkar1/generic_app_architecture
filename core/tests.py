from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from core.models import Organization

class OrganizationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()

    def test_organization_singleton(self):
        # Create first organization
        org1 = Organization.objects.create(
            name="Org 1",
            owner_name="Owner 1",
            email="org1@example.com"
        )
        self.assertEqual(Organization.objects.count(), 1)

        # Attempt to create second organization
        org2 = Organization(
            name="Org 2",
            owner_name="Owner 2",
            email="org2@example.com"
        )
        with self.assertRaises(ValidationError):
            org2.full_clean()
        
        with self.assertRaises(ValidationError):
            org2.save()

    def test_middleware_redirection_and_forced_setup(self):
        self.client.login(username='testuser', password='password123')
        
        # Accessing dashboard should redirect to setup page since no organization exists
        dashboard_url = '/'
        response = self.client.get(dashboard_url)
        self.assertRedirects(response, reverse('core:organization_create'))

        # Accessing setup page should render correctly (200 OK)
        setup_url = reverse('core:organization_create')
        response = self.client.get(setup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to ERP Framework")

        # Create organization via setup page
        post_data = {
            'name': 'Test Corp',
            'owner_name': 'John Doe',
            'email': 'john@testcorp.com',
            'phone': '1234567890',
            'gstin': '22AAAAA0000A1Z5',
            'license_number': 'LIC-999',
            'address': '123 Main St'
        }
        response = self.client.post(setup_url, data=post_data)
        self.assertEqual(response.status_code, 302) # Redirects to settings_dashboard
        self.assertEqual(Organization.objects.count(), 1)

        # Now dashboard should load successfully without redirection
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, 200)
