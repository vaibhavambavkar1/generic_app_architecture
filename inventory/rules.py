from core.rules.registry import RuleEngine

@RuleEngine.register_condition('is_manager_or_admin')
def is_manager_or_admin(context):
    """Checks if the user executing the transition is a superuser or belongs to Managers group."""
    user = context.get('user')
    if not user:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='Managers').exists()

@RuleEngine.register_action('replenish_item_stock')
def replenish_item_stock(context):
    """
    Increments the stock levels of InventoryItems and revalues their unit cost
    using the Weighted Average Cost (WAC) method.
    """
    purchase_order = context.get('instance')
    if not purchase_order:
        return
        
    total_received_amount = 0.00
    for line in purchase_order.lines.all():
        item = line.item
        current_stock = item.stock_level
        current_price = item.unit_price
        
        received_stock = line.received_quantity if line.received_quantity is not None else line.quantity
        received_price = line.received_unit_price if line.received_unit_price is not None else line.unit_price
        
        new_stock = current_stock + received_stock
        if new_stock > 0:
            # WAC Formula: (Current Value + Received Value) / New Stock
            new_price = ((current_stock * current_price) + (received_stock * received_price)) / new_stock
            item.unit_price = new_price
            
        item.stock_level = new_stock
        item.save()
        total_received_amount += float(received_stock * received_price)
        
    purchase_order.total_amount = total_received_amount
    purchase_order.save()
