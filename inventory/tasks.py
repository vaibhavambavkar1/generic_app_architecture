from celery import shared_task
from django.db.models import F
from .models import InventoryItem

@shared_task
def check_low_stock_levels():
    """
    Scans the inventory items and identifies all SKUs that have dropped
    below their defined reorder threshold.
    """
    low_stock_items = InventoryItem.objects.filter(stock_level__lte=F('reorder_threshold'))
    alert_count = low_stock_items.count()
    
    if alert_count > 0:
        skus = [f"{item.name} ({item.sku}): {item.stock_level}/{item.reorder_threshold}" for item in low_stock_items]
        alert_msg = f"[LOW STOCK ALERT] {alert_count} items need restock:\n" + "\n".join(skus)
        print(alert_msg)
    else:
        print("[INFO] All inventory stock levels are healthy.")
        
    return alert_count
