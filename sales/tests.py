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
