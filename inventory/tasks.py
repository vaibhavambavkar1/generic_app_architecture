from celery import shared_task
from django.db.models import F
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import InventoryItem, PurchaseOrder
from core.models import State, Transition

@shared_task
def check_low_stock_levels():
    """
    Scans the inventory items and identifies all SKUs that have dropped
    below their defined reorder threshold, then emails the admin.
    """
    low_stock_items = InventoryItem.objects.filter(stock_level__lte=F('reorder_threshold'))
    alert_count = low_stock_items.count()
    
    if alert_count > 0:
        skus = [f"{item.name} ({item.sku}): {item.stock_level}/{item.reorder_threshold}" for item in low_stock_items]
        alert_msg = f"[LOW STOCK ALERT] {alert_count} items need restock:\n" + "\n".join(skus)
        print(alert_msg)
        
        send_mail(
            subject=f'Low Stock Alert: {alert_count} items need attention',
            message=alert_msg,
            from_email='system@quantumglobal.com',
            recipient_list=['admin@quantumglobal.com'],
            fail_silently=False,
        )
    else:
        print("[INFO] All inventory stock levels are healthy.")
        
    return alert_count

@shared_task
def auto_transition_overdue_pos():
    """
    Finds PurchaseOrders that have been 'Approved' for more than 7 days,
    and transitions them to an 'Overdue' state, or simply logs them.
    (Assuming 'Approved' is waiting for receiving).
    """
    # Assuming 'Approved' state exists and indicates waiting for receiving
    # Let's see if we have an Overdue state. If not, we just log them for now.
    cutoff_date = timezone.now() - timedelta(days=7)
    
    # We filter POs that are in 'Approved' state and were created before the cutoff date
    # In a real app we'd track the state entry time, but created_at is fine for demonstration
    overdue_pos = PurchaseOrder.objects.filter(
        workflow_state__name='Approved',
        created_at__lte=cutoff_date
    )
    
    count = overdue_pos.count()
    if count > 0:
        po_numbers = [po.po_number for po in overdue_pos]
        alert_msg = f"[OVERDUE PO ALERT] {count} Approved POs are older than 7 days and haven't been received: {', '.join(po_numbers)}"
        print(alert_msg)
        
        send_mail(
            subject=f'Overdue PO Alert: {count} Purchase Orders Pending',
            message=alert_msg,
            from_email='system@quantumglobal.com',
            recipient_list=['admin@quantumglobal.com'],
            fail_silently=True,
        )
        
        # Here we would normally transition them if there is a valid transition:
        # e.g., po.transition_to(overdue_transition, None)
    else:
        print("[INFO] No overdue Purchase Orders found.")
        
    return count

