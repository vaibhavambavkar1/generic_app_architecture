from django.test import TestCase
from decimal import Decimal
from django.utils import timezone

from .models import (
    PurchaseRequest, PurchaseRequestItem, 
    StorePurchaseOrder, StorePOLineItem, 
    GoodsReceiptNote, GRNLineItem
)
from generic_store_mgmt.models import Product, UnitOfMeasure
from inventory.models import Warehouse, Supplier, StockLedger
from finance.models import Account, AccountCategory, JournalEntry

class PurchasingWorkflowTests(TestCase):
    
    def setUp(self):
        # Master Data
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")
        self.product = Product.objects.create(name="Test Item", uom=self.uom)
        self.warehouse = Warehouse.objects.create(name="Main Hub")
        self.supplier = Supplier.objects.create(name="Acme Corp", contact_email="acme@example.com")
        
        # Finance Accounts
        self.inventory_acc = Account.objects.create(
            code="1200", name="Inventory Asset", category=AccountCategory.ASSET
        )
        self.ap_acc = Account.objects.create(
            code="2000", name="Accounts Payable", category=AccountCategory.LIABILITY
        )

    def test_purchase_request_transitions(self):
        """Test the FSM transitions for Purchase Request"""
        pr = PurchaseRequest.objects.create(
            request_number="PR-001",
            department="IT",
            expected_date=timezone.now().date()
        )
        self.assertEqual(pr.status, "Draft")
        
        pr.submit_pr()
        self.assertEqual(pr.status, "Submitted")
        
        pr.approve_pr()
        self.assertEqual(pr.status, "Approved")

    def test_grn_receive_goods_creates_ledger_and_journal(self):
        """
        Test that receiving goods on a GRN:
        1. Updates the PO status
        2. Creates StockLedger entry
        3. Creates automated JournalEntry
        """
        # Create PO
        po = StorePurchaseOrder.objects.create(
            po_number="PO-100",
            supplier=self.supplier,
            warehouse=self.warehouse,
            expected_delivery=timezone.now().date()
        )
        po.issue_po()
        self.assertEqual(po.status, "Issued")
        
        # Create PO Line
        po_line = StorePOLineItem.objects.create(
            po=po,
            product=self.product,
            quantity=10,
            unit_price=Decimal("50.00")
        )
        
        # Create GRN
        grn = GoodsReceiptNote.objects.create(
            grn_number="GRN-100",
            purchase_order=po
        )
        
        # Create GRN Line
        grn_line = GRNLineItem.objects.create(
            grn=grn,
            po_line=po_line,
            product=self.product,
            expected_quantity=10,
            received_quantity=10
        )
        
        # Action: Receive Goods
        grn.receive_goods()
        grn.save()
        
        # Assert PO transitioned
        po.refresh_from_db()
        self.assertEqual(po.status, "Partially Received")
        
        # Assert StockLedger updated
        stock_entries = StockLedger.objects.filter(reference_document="GRN-100")
        self.assertEqual(stock_entries.count(), 1)
        self.assertEqual(stock_entries.first().quantity, 10)
        self.assertEqual(stock_entries.first().transaction_type, "PURCHASE")
        
        # Assert JournalEntry created automatically
        je = JournalEntry.objects.filter(reference="GRN-100").first()
        self.assertIsNotNone(je)
        self.assertTrue(je.is_posted)
        
        # Verify double-entry amounts
        # Total value = 10 * 50 = 500
        self.assertEqual(je.lines.count(), 2)
        
        inventory_line = je.lines.get(account=self.inventory_acc)
        self.assertEqual(inventory_line.debit, Decimal("500.00"))
        self.assertEqual(inventory_line.credit, Decimal("0.00"))
        
        ap_line = je.lines.get(account=self.ap_acc)
        self.assertEqual(ap_line.credit, Decimal("500.00"))
        self.assertEqual(ap_line.debit, Decimal("0.00"))
        self.assertEqual(ap_line.supplier, self.supplier)
