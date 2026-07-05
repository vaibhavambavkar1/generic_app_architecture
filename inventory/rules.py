from core.rules.registry import RuleEngine
from .tasks import sync_stock_to_external_warehouse

@RuleEngine.register_condition('is_valid_po_amount')
def is_valid_po_amount(context):
    """Ensure PO amount is logical before allowing approval."""
    instance = context.get('instance')
    return instance.total_cost > 0

@RuleEngine.register_action('update_inventory_stock')
def update_inventory_stock(context):
    """Increase stock level once PO is approved."""
    instance = context.get('instance')
    
    item = instance.item
    item.stock_quantity += instance.quantity
    item.save(update_fields=['stock_quantity'])
    
    # Fire the asynchronous background task!
    # Using .delay() puts it in the Redis queue for the celery-worker to pick up instantly
    sync_stock_to_external_warehouse.delay(
        item_id=item.id,
        new_quantity=item.stock_quantity,
        po_id=instance.id
    )
