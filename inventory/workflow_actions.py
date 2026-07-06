from core.rules.registry import RuleEngine
from .services import LedgerService

@RuleEngine.register_action('receive_po_stock')
def receive_po_stock(context):
    """
    Action triggered when a PurchaseOrder transitions to 'Received'.
    Iterates over all line items and logs a ledger transaction for each.
    """
    po = context.get('instance')
    user = context.get('user')
    
    if not po or not po.destination_warehouse:
        raise ValueError("Cannot receive stock without a valid PO and Destination Warehouse.")
        
    for line_item in po.items.all():
        LedgerService.record_stock_transaction(
            item=line_item.item,
            warehouse=po.destination_warehouse,
            quantity_change=line_item.quantity,
            transaction_type='IN_PO',
            reference_document=po.po_number or f"PO-{po.id}",
            user=user,
            notes=f"Auto-received from PO transition."
        )

@RuleEngine.register_condition('po_requires_manager_approval')
def po_requires_manager_approval(context):
    """
    Condition: If PO total_amount > 50,000, it requires Manager approval.
    """
    po = context.get('instance')
    if po and po.total_amount > 50000:
        return True
    return False
