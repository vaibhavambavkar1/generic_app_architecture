from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Workflow, State, Organization
from itam.models import AssetCategory, Asset, AssetAssignment, MaintenanceRecord
from hrms.models import Employee
from decimal import Decimal
from datetime import date

User = get_user_model()

class ITAMTests(TestCase):
    def setUp(self):
        # Bypass Organization Setup redirect
        Organization.objects.create(
            name='Test Org',
            owner_name='Test Owner',
            email='test@example.com'
        )

        # Create user & employee for assignments
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpassword')
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='EMP-001',
            department='IT'
        )

        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

        # Create Category
        self.category = AssetCategory.objects.create(name='Laptops')

        # Setup Workflow
        self.workflow = Workflow.objects.create(name='IT Asset Tracking', model_name='itam.Asset')
        self.state_available = State.objects.create(name='Available', workflow=self.workflow, is_initial=True)
        self.state_in_use = State.objects.create(name='In Use', workflow=self.workflow)
        self.state_maintenance = State.objects.create(name='Under Maintenance', workflow=self.workflow)
        self.state_retired = State.objects.create(name='Retired', workflow=self.workflow)

        # Create Asset
        self.asset = Asset.objects.create(
            name='MacBook Pro M2',
            category=self.category,
            serial_number='SN123456789',
            purchase_cost=Decimal('2000.00'),
            status='Available',
            workflow_state=self.state_available
        )

    # --- 1. Model & Creation Tests ---
    def test_asset_creation_and_barcode_auto_generation(self):
        """Test Asset model creation and automatic barcode assignment."""
        self.assertEqual(self.asset.name, 'MacBook Pro M2')
        # Check auto-generated barcode
        self.assertEqual(self.asset.barcode, 'AST-SN123456789')
        self.assertEqual(str(self.asset), 'MacBook Pro M2 (AST-SN123456789)')

    # --- 2. State Machine Tests ---
    def test_asset_assignment_transition(self):
        """Test FSM transition from Available to In Use."""
        self.asset.assign_asset(self.employee)
        self.asset.save()
        self.assertEqual(self.asset.status, 'In Use')
        self.assertEqual(self.asset.current_assignee, self.employee)

    def test_asset_return_transition(self):
        """Test FSM transition from In Use back to Available."""
        self.asset.assign_asset(self.employee)
        self.asset.save()
        
        self.asset.return_asset()
        self.asset.save()
        
        self.assertEqual(self.asset.status, 'Available')
        self.assertIsNone(self.asset.current_assignee)

    def test_asset_maintenance_transition(self):
        """Test FSM transition to Under Maintenance."""
        self.asset.send_to_maintenance()
        self.asset.save()
        self.assertEqual(self.asset.status, 'Under Maintenance')

    def test_asset_retire_transition(self):
        """Test FSM transition to Retired."""
        self.asset.assign_asset(self.employee)
        self.asset.save()
        
        self.asset.retire_asset()
        self.asset.save()
        
        self.assertEqual(self.asset.status, 'Retired')
        self.assertIsNone(self.asset.current_assignee)

    # --- 3. View Tests ---
    def test_dashboard_view(self):
        """Test ITAM Dashboard rendering."""
        response = self.client.get(reverse('itam:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itam/dashboard.html')
        self.assertIn('total_assets', response.context)

    def test_asset_list_view(self):
        """Test Asset Register view."""
        response = self.client.get(reverse('itam:asset_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'itam/asset_list.html')
        self.assertContains(response, 'MacBook Pro M2')

    def test_asset_create_view(self):
        """Test creating a new asset via view/form."""
        data = {
            'name': 'Dell XPS 15',
            'category': self.category.id,
            'serial_number': 'XPS987654',
            'purchase_cost': '1500.00'
        }
        response = self.client.post(reverse('itam:asset_create'), data)
        self.assertEqual(response.status_code, 302)  # redirect to list
        self.assertTrue(Asset.objects.filter(serial_number='XPS987654').exists())

    def test_asset_detail_assign_view(self):
        """Test assignment transition via POST on detail view."""
        data = {
            'method': 'assign_asset',
            'employee_id': self.employee.id
        }
        response = self.client.post(reverse('itam:asset_detail', args=[self.asset.id]), data)
        self.assertEqual(response.status_code, 302)
        
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, 'In Use')
        self.assertEqual(self.asset.workflow_state.name, 'In Use')
        self.assertEqual(self.asset.current_assignee, self.employee)
        
        # Verify Assignment record created
        self.assertTrue(AssetAssignment.objects.filter(asset=self.asset, employee=self.employee).exists())

    def test_export_asset_label(self):
        """Test the Barcode/QR Code PDF generation endpoint."""
        response = self.client.get(reverse('itam:export_asset_label', args=[self.asset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.has_header('Content-Disposition'))
