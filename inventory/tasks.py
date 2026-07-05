import time
from celery import shared_task

@shared_task
def sync_stock_to_external_warehouse(item_id, new_quantity, po_id):
    """
    Simulates a heavy, long-running background task 
    (e.g., calling an external vendor's API or a legacy warehouse system).
    """
    print(f"\n[{'='*40}]")
    print(f"[CELERY WORKER] Starting background sync for Item #{item_id} (Triggered by PO #{po_id})")
    print(f"[CELERY WORKER] Connecting to legacy warehouse API...")
    
    # Simulate a slow network request (5 seconds)
    time.sleep(5)
    
    print(f"[CELERY WORKER] Successfully synced new stock quantity ({new_quantity}) for Item #{item_id}.")
    print(f"[{'='*40}]\n")
    
    return True
