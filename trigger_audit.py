import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_framework.settings')
django.setup()

from inventory.models import PurchaseOrder
from django.contrib.auth.models import User

po = PurchaseOrder.objects.first()

# Mock a system admin updating the quantity directly
user = User.objects.first()
po._audit_user_id = user.id if user else None

old_quantity = po.quantity
new_quantity = po.quantity + 50

print(f"Modifying PO #{po.id} quantity from {old_quantity} to {new_quantity}...")
po.quantity = new_quantity
po.save()

print("Database save completed successfully.")
print("The 'write_audit_log' Celery task should now execute in the background!")
