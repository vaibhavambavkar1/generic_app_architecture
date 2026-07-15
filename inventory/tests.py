from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Workflow, State, Organization
from inventory.models import Supplier, InventoryItem, PurchaseOrder, POLineItem, InventoryItemPriceLog
from decimal import Decimal

User = get_user_model()

class InventoryTests(TestCase):
    def setUp(self):
        # Bypass Organization Setup redirect
        Organization.objects.create(
            name='Test Org',
            owner_name='Test Owner',
            email='test@example.com'
        )

        # Create user
        self.user = User.objects.create_user(username='invuser', email='inv@test.com', password='testpassword')
        
        self.client = Client()
        self.client.login(username='invuser', password='testpassword')

        # Setup Workflow
        self.workflow = Workflow.objects.create(name='Purchase Order', model_name='inventory.PurchaseOrder')
        self.state_draft = State.objects.create(name='Draft', workflow=self.workflow, is_initial=True)
        self.state_submitted = State.objects.create(name='Submitted', workflow=self.workflow)
        self.state_approved = State.objects.create(name='Approved', workflow=self.workflow)
        self.state_received = State.objects.create(name='Received', workflow=self.workflow)

        # Create Supplier
        self.supplier = Supplier.objects.create(
            name='Acme Corp',
            contact_email='acme@example.com',
            phone='1234567890'
        )

        # Create Inventory Item
        self.item = InventoryItem.objects.create(
            name='Widget A',
            stock_level=100,
            unit_price=Decimal('10.50')
        )

        # Create PO
        self.po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            status='Draft',
            workflow_state=self.state_draft
        )

        # Create PO Line Item
        self.po_line = POLineItem.objects.create(
            purchase_order=self.po,
            item=self.item,
            quantity=50,
            unit_price=Decimal('10.00')
        )

    # --- 1. Model Tests ---
    def test_inventory_item_creation(self):
        """Test InventoryItem creation, auto-SKU, and barcode generation."""
        self.assertTrue(self.item.sku.startswith('SKU-'))
        self.assertTrue(bool(self.item.barcode))
        self.assertTrue(bool(self.item.qr_code))
        self.assertEqual(self.item.name, 'Widget A')
        
    def test_price_log_creation_on_update(self):
        """Test that a price log is created when unit_price changes."""
        initial_log_count = InventoryItemPriceLog.objects.filter(item=self.item).count()
        self.assertEqual(initial_log_count, 1) # Created on initial save
        
        # Change price
        self.item.unit_price = Decimal('12.00')
        self.item.save()
        
        self.assertEqual(InventoryItemPriceLog.objects.filter(item=self.item).count(), 2)
        latest_log = InventoryItemPriceLog.objects.filter(item=self.item).first()
        self.assertEqual(latest_log.price, Decimal('12.00'))

    def test_po_auto_number(self):
        """Test auto-generation of PO numbers."""
        self.assertTrue(self.po.po_number.startswith('PO-'))
        self.assertTrue(len(self.po.po_number) > 5)

    def test_poline_subtotal(self):
        """Test subtotal calculation for PO Line Items."""
        self.assertEqual(self.po_line.subtotal, Decimal('500.00'))

    # --- 2. State Machine Tests (PO) ---
    def test_po_submit_transition(self):
        self.po.fsm_submit()
        self.po.save()
        self.assertEqual(self.po.status, 'Submitted')

    def test_po_approve_transition(self):
        self.po.fsm_submit()
        self.po.fsm_approve()
        self.po.save()
        self.assertEqual(self.po.status, 'Approved')

    def test_po_receive_transition(self):
        self.po.fsm_submit()
        self.po.fsm_approve()
        self.po.fsm_receive()
        self.po.save()
        self.assertEqual(self.po.status, 'Received')

    # --- 3. View Tests ---
    def test_dashboard_view(self):
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/dashboard.html')

    def test_item_list_view(self):
        response = self.client.get(reverse('inventory:item_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Widget A')

    def test_po_list_view(self):
        response = self.client.get(reverse('inventory:po_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.po.po_number)
