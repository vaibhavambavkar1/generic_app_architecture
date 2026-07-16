from django.test import TestCase
from decimal import Decimal
from django.utils import timezone

from .models import (
    Quotation, QuotationLineItem,
    SalesOrder, POSInvoice, POSLineItem
)
from generic_store_mgmt.models import Product, UnitOfMeasure
from inventory.models import Warehouse, StockLedger
from crm.models import Customer
from finance.models import Account, AccountCategory, JournalEntry

class SalesWorkflowTests(TestCase):
    
    def setUp(self):
        # Master Data Setup
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")
        self.product = Product.objects.create(name="Retail Item", uom=self.uom, selling_price=Decimal("150.00"))
        self.warehouse = Warehouse.objects.create(name="Storefront")
        self.customer = Customer.objects.create(name="Walk-in Customer", email="walkin@example.com")
        
        # Finance Accounts Setup (Cash & Revenue)
        self.cash_acc = Account.objects.create(
            code="1000", name="Cash on Hand", category=AccountCategory.ASSET
        )
        self.revenue_acc = Account.objects.create(
            code="4000", name="Sales Revenue", category=AccountCategory.REVENUE
        )

    def test_quotation_fsm_transitions(self):
        """Test FSM transitions for B2B Quotation."""
        quote = Quotation.objects.create(
            quote_number="QT-001",
            customer=self.customer,
            valid_until=timezone.now().date()
        )
        self.assertEqual(quote.status, "Draft")
        
        quote.send_quote()
        self.assertEqual(quote.status, "Sent")
        
        quote.accept_quote()
        self.assertEqual(quote.status, "Accepted")

    def test_sales_order_fsm_transitions(self):
        """Test FSM transitions for Sales Order."""
        order = SalesOrder.objects.create(
            so_number="SO-001",
            customer=self.customer,
            warehouse=self.warehouse,
            expected_dispatch_date=timezone.now().date()
        )
        self.assertEqual(order.status, "Draft")
        
        order.confirm_order()
        self.assertEqual(order.status, "Confirmed")
        
        order.ship_order()
        self.assertEqual(order.status, "Shipped")

    def test_pos_invoice_process_payment_ledger_and_journal(self):
        """
        Test that processing a POS payment correctly:
        1. Marks invoice as paid
        2. Injects negative StockLedger entries (inventory out)
        3. Creates double-entry JournalEntry for Cash & Revenue
        """
        # Create POS Invoice
        invoice = POSInvoice.objects.create(
            invoice_number="INV-POS-001",
            customer=self.customer,
            warehouse=self.warehouse,
            payment_method="CASH",
            total_amount=Decimal("300.00")
        )
        
        # Add 2 items (Quantity 2 * 150 = 300)
        POSLineItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=2,
            unit_price=Decimal("150.00"),
            line_total=Decimal("300.00")
        )
        
        # Action: Process Payment (Atomic Checkout)
        invoice.process_payment()
        invoice.refresh_from_db()
        
        # Assert Invoice Status
        self.assertTrue(invoice.is_paid)
        
        # Assert Stock Ledger (Inventory Out)
        stock_entries = StockLedger.objects.filter(reference_document="INV-POS-001")
        self.assertEqual(stock_entries.count(), 1)
        self.assertEqual(stock_entries.first().transaction_type, "SALES")
        # Ensure quantity is strictly negative for outgoing stock!
        self.assertEqual(stock_entries.first().quantity, -2)
        
        # Assert Journal Entry (Finance)
        je = JournalEntry.objects.filter(reference="INV-POS-001").first()
        self.assertIsNotNone(je)
        self.assertTrue(je.is_posted)
        self.assertEqual(je.lines.count(), 2)
        
        # Verify Cash is Debited (Asset Increases)
        cash_line = je.lines.get(account=self.cash_acc)
        self.assertEqual(cash_line.debit, Decimal("300.00"))
        self.assertEqual(cash_line.credit, Decimal("0.00"))
        
        # Verify Revenue is Credited (Revenue Increases)
        revenue_line = je.lines.get(account=self.revenue_acc)
        self.assertEqual(revenue_line.credit, Decimal("300.00"))
        self.assertEqual(revenue_line.debit, Decimal("0.00"))

from django.urls import reverse
from django.contrib.auth import get_user_model

class SalesModalFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password123')
        self.client.force_login(self.user)
        from core.models import Organization
        Organization.objects.create(name="Test Org", owner_name="Owner", email="owner@test.com")
        
        self.customer = Customer.objects.create(name="Test Customer")
        self.warehouse = Warehouse.objects.create(name="Test Warehouse")
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")

    def test_quotation_create_modal_get(self):
        url = reverse('sales:quotation_create_modal')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertTemplateUsed(response, 'sales/quotation_create_modal.html')

    def test_quotation_create_modal_post_success(self):
        url = reverse('sales:quotation_create_modal')
        data = {
            'quote_number': 'QT-NEW-001',
            'customer': self.customer.id,
            'valid_until': '2027-01-01',
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertTrue(Quotation.objects.filter(quote_number='QT-NEW-001').exists())
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertTrue('HX-Redirect' in response)
        
    def test_sales_order_create_modal_get(self):
        url = reverse('sales:sales_order_create_modal')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertTemplateUsed(response, 'sales/sales_order_create_modal.html')

    def test_sales_order_create_modal_post_success(self):
        url = reverse('sales:sales_order_create_modal')
        data = {
            'so_number': 'SO-NEW-001',
            'customer': self.customer.id,
            'warehouse': self.warehouse.id,
            'expected_dispatch_date': '2027-01-01',
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertTrue(SalesOrder.objects.filter(so_number='SO-NEW-001').exists())
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertTrue('HX-Redirect' in response)
