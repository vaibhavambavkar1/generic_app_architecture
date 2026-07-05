import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_framework.settings')
django.setup()

from inventory.models import Item, PurchaseOrder
from core.models import Workflow, State

print("Seeding database...")

# Ensure workflow exists
wf, _ = Workflow.objects.get_or_create(model_name='PurchaseOrder', name='PO Workflow')
draft, _ = State.objects.get_or_create(workflow=wf, name='Draft', is_initial=True)
pending, _ = State.objects.get_or_create(workflow=wf, name='Pending Approval')
approved, _ = State.objects.get_or_create(workflow=wf, name='Approved', is_final=True)

# Create Items
items = []
for i in range(1, 21):
    item, _ = Item.objects.get_or_create(sku=f"SKU-{1000+i}", defaults={'name': f"Demo Component {i}", 'stock_quantity': random.randint(10, 100)})
    items.append(item)

# Create POs
PurchaseOrder.objects.all().delete() # clean up
for i in range(1, 155): # Seed 154 records
    item = random.choice(items)
    po = PurchaseOrder.objects.create(
        item=item,
        quantity=random.randint(1, 50),
        total_cost=Decimal(random.randint(10000, 500000)) / 100
    )
    po.workflow_state = random.choice([draft, pending, approved])
    po.save()

print("Successfully seeded 20 items and 154 Purchase Orders.")
