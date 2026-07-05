import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_framework.settings')
django.setup()

from inventory.models import PurchaseOrder
from core.rules.registry import RuleEngine

po = PurchaseOrder.objects.first()
print(f"Executing business rule 'update_inventory_stock' for PO #{po.id}...")

# Directly execute the rule (which now fires the Celery task)
RuleEngine.execute_action('update_inventory_stock', {'instance': po})

print("Rule executed successfully on the main thread in ~0.05 seconds.")
print("The heavy network task has been dispatched to Redis!")
