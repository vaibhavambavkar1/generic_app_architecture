from django.db import transaction
from django.db.models import F
from .models import StockLedger, StockLevel, Item

class InsufficientStockError(Exception):
    """Raised when an outbound transaction drops stock below zero."""
    pass

class LedgerService:
    @staticmethod
    @transaction.atomic
    def record_stock_transaction(item, warehouse, quantity_change, transaction_type, reference_document, location=None, user=None, notes=""):
        """
        Records an immutable ledger entry and securely updates cache tables atomically.
        Utilizes DB-level row locks (select_for_update) to guarantee consistency 
        during high-concurrency WMS environments.
        """
        if quantity_change == 0:
            raise ValueError("Quantity change cannot be zero.")
            
        # 1. Update or Create localized StockLevel Cache
        # select_for_update() guarantees no other thread can read/modify this row until commit
        stock_level, created = StockLevel.objects.select_for_update().get_or_create(
            item=item,
            warehouse=warehouse,
            location=location,
            defaults={'quantity': 0}
        )
        
        # 2. Guard clause against negative inventory
        if stock_level.quantity + quantity_change < 0:
            raise InsufficientStockError(
                f"Insufficient stock for {item.sku} at {warehouse.name}. "
                f"Current: {stock_level.quantity}, Requested: {-quantity_change}"
            )
            
        stock_level.quantity += quantity_change
        stock_level.save(update_fields=['quantity', 'last_updated'])
        
        # 3. Update Global Item Cache
        item_locked = Item.objects.select_for_update().get(id=item.id)
        item_locked.stock_quantity += quantity_change
        item_locked.save(update_fields=['stock_quantity'])
        
        # 4. Insert Immutable Ledger Entry
        entry = StockLedger.objects.create(
            item=item,
            warehouse=warehouse,
            location=location,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            reference_document=reference_document,
            created_by=user,
            notes=notes
        )
        
        return entry
