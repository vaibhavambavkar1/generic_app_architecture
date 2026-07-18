from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from courier.models import Waybill, DispatchManifest, ManifestItem, ProofOfDelivery
from crm.models import Customer
from logistics_core.models import Zone, ServiceType, Route
from fleet_mgmt.models import Vehicle
from hrms.models import Employee
from finance.models import JournalEntry, JournalEntryLine, Account
from core.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()

class CourierManagementTests(TestCase):
    def setUp(self):
        # Create foundational entities
        Organization.objects.create(name="Test Org", owner_name="Test Owner", email="test@org.com")
        self.user = User.objects.create_user(username='testdisp', password='password123')
        self.client_http = Client()
        self.client_http.force_login(self.user)

        self.customer = Customer.objects.create(name="Acme Corp", email="contact@acme.com")
        self.zone_origin = Zone.objects.create(name="North Zone", code="NZ-01")
        self.zone_dest = Zone.objects.create(name="South Zone", code="SZ-01")
        self.service_type = ServiceType.objects.create(name="Express Delivery")
        
        self.driver = Employee.objects.create(
            user=self.user,
            employee_id="EMP-DRV-001",
            department="Logistics"
        )
        self.vehicle = Vehicle.objects.create(
            registration_number="TRK-999", 
            vehicle_type='TRUCK',
            capacity_kg=Decimal('5000.00')
        )
        
        # Setup Finance Accounts for testing signals
        Account.objects.create(code='1100', name='Accounts Receivable', category='ASSET')
        Account.objects.create(code='4000', name='Freight Revenue', category='REVENUE')

    def test_waybill_pricing_calculation(self):
        """Test that Waybill save() method calculates chargeable weight and price correctly."""
        waybill = Waybill.objects.create(
            waybill_number="WB-TEST-001",
            sender=self.customer,
            receiver_name="John Doe",
            receiver_phone="1234567890",
            receiver_address="123 Test St",
            origin_zone=self.origin_zone if hasattr(self, 'origin_zone') else self.zone_origin,
            destination_zone=self.zone_dest,
            service_type=self.service_type,
            weight_kg=Decimal('10.00'),
            volume_m3=Decimal('0.10') # 0.10 m3 * 200 = 20 kg volumetric weight
        )
        # Volumetric weight should be higher (20.00) than actual weight (10.00)
        self.assertEqual(waybill.chargeable_weight, Decimal('20.00'))
        
        # Express base rate = 25, per kg = 8. Total = 25 + (20 * 8) = 185
        self.assertEqual(waybill.price, Decimal('185.00'))

    def test_dispatch_manifest_workflow(self):
        """Test FSM transitions for Dispatch Manifest and cascading to Waybills."""
        waybill = Waybill.objects.create(
            waybill_number="WB-TEST-002",
            receiver_name="Jane Doe",
            receiver_phone="0987654321",
            receiver_address="456 Elm St",
            weight_kg=Decimal('5.00'),
            status='At Hub'
        )

        manifest = DispatchManifest.objects.create(
            manifest_number="MNF-TEST-001",
            driver=self.driver,
            vehicle=self.vehicle
        )
        
        # Add waybill to manifest
        ManifestItem.objects.create(manifest=manifest, waybill=waybill, sequence=1)
        
        # Dispatch the manifest
        manifest.dispatch()
        manifest.save()
        
        self.assertEqual(manifest.status, 'Dispatched')
        
        # Verify cascaded transition to Waybill
        waybill.refresh_from_db()
        self.assertEqual(waybill.status, 'In Transit')

    def test_htmx_add_waybill_to_manifest(self):
        """Test the HTMX endpoint for adding a waybill."""
        waybill = Waybill.objects.create(
            waybill_number="SCANME",
            receiver_name="Bob Smith",
            receiver_phone="1111111111",
            receiver_address="789 Pine St",
            status='Draft'
        )
        manifest = DispatchManifest.objects.create(
            manifest_number="MNF-TEST-002",
            driver=self.driver,
            vehicle=self.vehicle
        )
        
        url = reverse('courier:add_waybill_to_manifest', args=[manifest.id])
        
        # Simulate HTMX POST
        response = self.client_http.post(url, {'waybill_number': 'SCANME'}, HTTP_HX_REQUEST='true')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SCANME')
        
        # Verify DB
        self.assertTrue(ManifestItem.objects.filter(manifest=manifest, waybill=waybill).exists())

    def test_waybill_delivery_financial_signal(self):
        """Test that delivering a Waybill triggers the AR Journal Entry generation."""
        waybill = Waybill.objects.create(
            waybill_number="WB-DELIVER-001",
            sender=self.customer,
            receiver_name="Alice",
            receiver_phone="222",
            receiver_address="Address",
            service_type=self.service_type,
            weight_kg=Decimal('10.00'),
            status='Out for Delivery' # Set to previous state
        )
        
        # Perform FSM transition
        waybill.mark_delivered()
        waybill.save()
        
        # Verify Financial Integration (Signal should create Journal Entry)
        je = JournalEntry.objects.filter(reference=waybill.waybill_number).first()
        self.assertIsNotNone(je)
        self.assertEqual(je.is_posted, True)
        
        # Verify lines
        ar_line = je.lines.filter(account__code='1100').first()
        revenue_line = je.lines.filter(account__code='4000').first()
        
        self.assertIsNotNone(ar_line)
        self.assertEqual(ar_line.debit, waybill.price)
        self.assertIsNotNone(revenue_line)
        self.assertEqual(revenue_line.credit, waybill.price)

    def test_waybill_pdf_generation_endpoint(self):
        """Test that the PDF generation view returns a PDF file response."""
        waybill = Waybill.objects.create(
            waybill_number="WB-PDF-001",
            receiver_name="Charlie",
            receiver_phone="333",
            receiver_address="PDF Lane"
        )
        
        url = reverse('courier:download_waybill_pdf', args=[waybill.id])
        response = self.client_http.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="Waybill_WB-PDF-001.pdf"'))
