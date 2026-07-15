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


from core.reports import BaseReport, ReportRegistry, ReportEngine, ReportExporter, ChartBuilder

class UserReport(BaseReport):
    name = "user_report"
    description = "Test report for users"
    model = User

    def get_fields(self):
        return {
            'username': 'Username',
            'is_staff': 'Is Staff',
            'id': 'ID'
        }

class ReportEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password123', email='admin@example.com')
        self.staff_user1 = User.objects.create_user(username='staff1', is_staff=True, password='password123')
        self.staff_user2 = User.objects.create_user(username='staff2', is_staff=True, password='password123')
        self.regular_user = User.objects.create_user(username='regular', is_staff=False, password='password123')
        
        # Register report
        ReportRegistry.register('user_report', UserReport)

    def test_report_execution_and_filtering(self):
        engine = ReportEngine()
        config = {
            'filters': [
                {'field': 'is_staff', 'operator': 'eq', 'value': True}
            ],
            'fields': ['username', 'id'],
            'sorting': [{'field': 'username', 'direction': 'asc'}]
        }
        
        # Run report
        data = engine.execute('user_report', self.user, config, use_cache=False)
        
        # 3 users should match (admin, staff1, staff2)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['username'], 'admin')

    def test_report_formulas(self):
        engine = ReportEngine()
        config = {
            'fields': ['username', 'id'],
            'formulas': {
                'double_id': 'id * 2'
            }
        }
        data = engine.execute('user_report', self.user, config, use_cache=False)
        for row in data:
            self.assertEqual(row['double_id'], row['id'] * 2)

    def test_report_group_by_and_aggregation(self):
        engine = ReportEngine()
        config = {
            'group_by': ['is_staff'],
            'aggregates': [
                {'field': 'id', 'function': 'count', 'alias': 'user_count'}
            ]
        }
        data = engine.execute('user_report', self.user, config, use_cache=False)
        # Should have 2 groups: is_staff=True (3 users) and is_staff=False (1 user, or 2 if Guardian AnonymousUser is present)
        self.assertEqual(len(data), 2)
        for row in data:
            if row['is_staff']:
                self.assertEqual(row['user_count'], 3)
            else:
                expected_count = 2 if User.objects.filter(username='AnonymousUser').exists() else 1
                self.assertEqual(row['user_count'], expected_count)

    def test_report_exports(self):
        engine = ReportEngine()
        config = {
            'fields': ['username', 'is_staff']
        }
        data = engine.execute('user_report', self.user, config, use_cache=False)
        headers = {'username': 'Username', 'is_staff': 'Is Staff'}
        
        # CSV Export
        csv_file = ReportExporter.to_csv(data, headers)
        self.assertTrue(csv_file.getvalue().startswith(b'Username,Is Staff'))

        # JSON Export
        json_file = ReportExporter.to_json(data)
        self.assertTrue(json_file.getvalue().startswith(b'['))

        # Excel Export
        xls_file = ReportExporter.to_excel(data, headers)
        self.assertTrue(xls_file.getvalue().startswith(b'PK'))

        # PDF Export
        pdf_file = ReportExporter.to_pdf(data, headers)
        self.assertTrue(pdf_file.getvalue().startswith(b'%PDF'))


class ReportUITestsCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password123', email='admin@example.com')
        from core.models import Organization
        self.org = Organization.objects.create(
            name="Org 1",
            owner_name="Owner 1",
            email="org1@example.com"
        )
        self.client = Client()
        self.client.login(username='admin', password='password123')
        ReportRegistry.register('user_report', UserReport)

    def test_report_builder_view(self):
        response = self.client.get(reverse('core:report_builder'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dynamic Report Builder")

    def test_load_report_fields_view(self):
        response = self.client.get(reverse('core:load_report_fields') + '?report_id=user_report')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select Fields to Display")

    def test_add_filter_row_view(self):
        response = self.client.get(reverse('core:add_filter_row') + '?report_id=user_report&index=1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "filter_field")

    def test_report_preview_view(self):
        post_data = {
            'report_id': 'user_report',
            'fields': ['username', 'id'],
        }
        response = self.client.post(reverse('core:report_preview'), data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin")

    def test_report_preview_view_invalid_fields(self):
        post_data = {
            'report_id': 'user_report',
            'fields': ['invalid_field_abc'],
        }
        response = self.client.post(reverse('core:report_preview'), data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Processing Configuration...")

    def test_save_and_execute_report_view(self):
        post_data = {
            'report_id': 'user_report',
            'report_name': 'Admin List',
            'config_json': '{"fields": ["username", "id"]}'
        }
        response = self.client.post(reverse('core:save_report'), data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin List")
        
        from core.models import SavedReport
        saved = SavedReport.objects.get(name='Admin List')
        self.assertEqual(saved.report_id, 'user_report')

        response = self.client.get(reverse('core:execute_saved_report', args=[saved.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin List")

        # Edit/Update Report Configuration
        update_data = {
            'report_id': 'user_report',
            'report_name': 'Updated Admin List',
            'config_json': '{"fields": ["username"]}',
            'saved_report_id': saved.pk
        }
        response = self.client.post(reverse('core:save_report'), data=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Updated Admin List")
        saved.refresh_from_db()
        self.assertEqual(saved.name, 'Updated Admin List')
        self.assertEqual(saved.config['fields'], ['username'])

        # Delete Report Configuration
        delete_response = self.client.post(reverse('core:delete_saved_report', args=[saved.pk]))
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(SavedReport.objects.filter(pk=saved.pk).exists())


class CoreSystemViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password123', email='admin@example.com')
        from core.models import Organization, AuditLog
        from django.contrib.contenttypes.models import ContentType
        self.org = Organization.objects.create(
            name="Org 1",
            owner_name="Owner 1",
            email="org1@example.com"
        )
        self.client = Client()
        self.client.login(username='admin', password='password123')

        # Create dummy AuditLog
        ct = ContentType.objects.get_for_model(Organization)
        AuditLog.objects.create(
            user=self.user,
            action='CREATE',
            content_type=ct,
            object_id=self.org.id,
            new_values={'name': 'Org 1'}
        )

    def test_audit_log_list_view(self):
        response = self.client.get(reverse('core:audit_logs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Audit Logs")
        self.assertContains(response, "Create")

    def test_global_search_view(self):
        # Test empty query
        response = self.client.get(reverse('core:global_search'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No results found")

        # Test matched query on Supplier
        from inventory.models import Supplier
        Supplier.objects.create(
            name="Mega Corp Supplier",
            contact_email="mega@corp.com",
            phone="9876543210"
        )
        response = self.client.get(reverse('core:global_search') + "?q=Mega")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mega Corp Supplier")
