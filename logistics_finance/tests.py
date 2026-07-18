from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from django.contrib.auth import get_user_model
from core.models import Organization
from finance.models import Account, JournalEntry, JournalEntryLine
from courier.models import Waybill
from freight.models import FreightBooking, FreightLeg
from wms_3pl.models import PutawayTask, Bin, Rack, Aisle, WarehouseZone
from inventory.models import Warehouse, Supplier
from crm.models import Customer
from generic_store_mgmt.models import Product, Category

User = get_user_model()

class LogisticsFinanceTests(TestCase):
    def setUp(self):
        # 1. Base Setup
        Organization.objects.create(name='Test Org', owner_name='Owner', email='test@org.com')
        self.user = User.objects.create_user(username='finuser', password='password123')
        self.client = Client()
        self.client.force_login(self.user)
        
        # 2. Financial Accounts setup
        self.ar_account = Account.objects.create(code='1100', name='Accounts Receivable', category='ASSET')
        self.ap_account = Account.objects.create(code='2000', name='Accounts Payable', category='LIABILITY')
        self.revenue_account = Account.objects.create(code='4000', name='Freight Revenue', category='REVENUE')
        self.expense_account = Account.objects.create(code='5000', name='Cost of Goods Sold', category='EXPENSE')
        
        # 3. Logistics Master Data
        self.customer = Customer.objects.create(name="Acme Corp")
        self.supplier = Supplier.objects.create(name="Carrier Co")
        
        # Waybill
        self.waybill = Waybill.objects.create(
            waybill_number="WB-TEST-001",
            sender=self.customer,
            receiver_name="John Doe",
            price=Decimal("150.00"),
            status="Out for Delivery"
        )
        
        # Freight Booking
        self.freight = FreightBooking.objects.create(
            booking_number="FRT-TEST-001",
            shipper=self.customer,
            status="Cleared"
        )
        self.leg = FreightLeg.objects.create(
            booking=self.freight,
            sequence=1,
            carrier=self.supplier,
            mode_of_transport="ROAD"
        )
        
        # WMS 3PL Setup
        self.warehouse = Warehouse.objects.create(name="Central WH")
        self.zone = WarehouseZone.objects.create(warehouse=self.warehouse, name="Zone A")
        self.aisle = Aisle.objects.create(zone=self.zone, code="A1")
        self.rack = Rack.objects.create(aisle=self.aisle, code="R1")
        self.bin = Bin.objects.create(rack=self.rack, code="B1")
        
        self.category = Category.objects.create(name="Electronics")
        from generic_store_mgmt.models import UnitOfMeasure
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")
        self.product = Product.objects.create(name="Laptop", category=self.category, sku="LAP-001", selling_price=Decimal("1000"), uom=self.uom)
        
        self.putaway = PutawayTask.objects.create(
            task_number="PT-TEST-001",
            client=self.customer,
            product=self.product,
            quantity=10,
            target_bin=self.bin,
            status="In Progress"
        )

    def test_waybill_delivery_signal(self):
        """Test AR generation when a Waybill is marked as Delivered."""
        self.waybill.status = 'Delivered'
        self.waybill.save()
        
        # Verify JE created
        je = JournalEntry.objects.filter(reference="WB-TEST-001").first()
        self.assertIsNotNone(je)
        self.assertEqual(je.entry_number, "JE-WAYBILL-WB-TEST-001")
        
        # Verify lines
        lines = je.lines.all()
        self.assertEqual(lines.count(), 2)
        debit_line = lines.get(debit__gt=0)
        credit_line = lines.get(credit__gt=0)
        
        self.assertEqual(debit_line.account.code, '1100')
        self.assertEqual(debit_line.debit, Decimal("150.00"))
        self.assertEqual(debit_line.customer, self.customer)
        
        self.assertEqual(credit_line.account.code, '4000')
        self.assertEqual(credit_line.credit, Decimal("150.00"))

    def test_freight_delivery_signal(self):
        """Test AR and AP generation when a FreightBooking is marked as Delivered."""
        self.freight.status = 'Delivered'
        self.freight.save()
        
        # Verify AR JE
        je_ar = JournalEntry.objects.filter(reference="FRT-TEST-001").first()
        self.assertIsNotNone(je_ar)
        self.assertEqual(je_ar.entry_number, "JE-FRT-AR-FRT-TEST-001")
        
        ar_lines = je_ar.lines.all()
        self.assertEqual(ar_lines.count(), 2)
        self.assertEqual(ar_lines.get(debit__gt=0).debit, Decimal("1500.00"))
        
        # Verify AP JE for Leg
        leg_ref = f"FRT-TEST-001-LEG-{self.leg.sequence}"
        je_ap = JournalEntry.objects.filter(reference=leg_ref).first()
        self.assertIsNotNone(je_ap)
        
        ap_lines = je_ap.lines.all()
        self.assertEqual(ap_lines.count(), 2)
        self.assertEqual(ap_lines.get(credit__gt=0).credit, Decimal("400.00"))
        self.assertEqual(ap_lines.get(credit__gt=0).account.code, '2000')
        self.assertEqual(ap_lines.get(credit__gt=0).supplier, self.supplier)

    def test_wms_putaway_signal(self):
        """Test AR generation for 3PL Handling Fee when a PutawayTask is Completed."""
        self.putaway.complete_putaway()
        self.putaway.save()
        
        je = JournalEntry.objects.filter(reference="PT-TEST-001").first()
        self.assertIsNotNone(je)
        self.assertEqual(je.entry_number, "JE-WMS-PT-TEST-001")
        
        # 10 units * 2.50 = 25.00
        lines = je.lines.all()
        self.assertEqual(lines.count(), 2)
        self.assertEqual(lines.get(debit__gt=0).debit, Decimal("25.00"))
        self.assertEqual(lines.get(credit__gt=0).credit, Decimal("25.00"))
        self.assertEqual(lines.get(debit__gt=0).customer, self.customer)

    def test_financial_dashboard_view(self):
        """Test the logistics finance dashboard view."""
        # Trigger signals to populate data
        self.waybill.status = 'Delivered'
        self.waybill.save()
        
        self.freight.status = 'Delivered'
        self.freight.save()
        
        url = reverse('logistics_finance:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'logistics_finance/dashboard.html')
        
        self.assertIn('ar_lines', response.context)
        self.assertIn('ap_lines', response.context)
        
        ar_lines = response.context['ar_lines']
        ap_lines = response.context['ap_lines']
        
        # One from Waybill, one from Freight AR
        self.assertTrue(any(line.debit == Decimal('150.00') for line in ar_lines))
        self.assertTrue(any(line.debit == Decimal('1500.00') for line in ar_lines))
        
        # One from Freight AP leg
        self.assertTrue(any(line.credit == Decimal('400.00') for line in ap_lines))
