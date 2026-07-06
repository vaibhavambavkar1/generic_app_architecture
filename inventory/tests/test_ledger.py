from django.test import TestCase
from inventory.models import Item, Warehouse, StockLevel, StockLedger
from inventory.services import LedgerService, InsufficientStockError

class LedgerServiceTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Laptop", sku="LAP-01", stock_quantity=0)
        self.warehouse = Warehouse.objects.create(name="Main Hub")
        
    def test_positive_transaction(self):
        """Test that receiving stock correctly caches and ledgers."""
        LedgerService.record_stock_transaction(
            item=self.item,
            warehouse=self.warehouse,
            quantity_change=10,
            transaction_type='IN_PO',
            reference_document='PO-001'
        )
        
        self.item.refresh_from_db()
        self.assertEqual(self.item.stock_quantity, 10)
        
        stock_level = StockLevel.objects.get(item=self.item, warehouse=self.warehouse)
        self.assertEqual(stock_level.quantity, 10)
        
        ledger_count = StockLedger.objects.filter(item=self.item).count()
        self.assertEqual(ledger_count, 1)

    def test_insufficient_stock_exception(self):
        """Test that selling more than what is available raises an exception and rolls back."""
        with self.assertRaises(InsufficientStockError):
            LedgerService.record_stock_transaction(
                item=self.item,
                warehouse=self.warehouse,
                quantity_change=-5, # Attempt to dispatch 5 laptops when we have 0
                transaction_type='OUT_SO',
                reference_document='SO-001'
            )
            
        # Verify no ledger was created
        ledger_count = StockLedger.objects.filter(item=self.item).count()
        self.assertEqual(ledger_count, 0)
