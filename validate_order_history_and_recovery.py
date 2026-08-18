import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_framework.settings')
django.setup()

from hotel_core.models import HotelBranch
from hotel_pos.models import Table, MenuItem, Order, OrderItem, MenuCategory, TaxConfiguration
from core.models import State, Workflow, AuditLog
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from hotel_pos.views import generate_bill, release_table, reopen_order, order_history, receipt_printer

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

print("--- Step 1: Set up Test Order ---")
branch = HotelBranch.objects.first()
if not branch:
    branch = HotelBranch.objects.create(name='Downtown Grand', code='DTG')

table, _ = Table.objects.get_or_create(branch=branch, number='HISTORY-1', defaults={'capacity': 4, 'is_active': True})
Order.objects.filter(table=table).delete()

cat, _ = MenuCategory.objects.get_or_create(branch=branch, name='Main')
menu_item, _ = MenuItem.objects.get_or_create(category=cat, name='Butter Chicken', defaults={'price': 300.0, 'is_active': True})

tax_cfg, _ = TaxConfiguration.objects.get_or_create(branch=branch, name='GST', defaults={'percentage': 5.0, 'is_active': True})

open_state = State.objects.filter(workflow__name='Order Lifecycle', name='Open').first()
served_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Served').first()

order = Order.objects.create(table=table, branch=branch, workflow_state=open_state)
OrderItem.objects.create(order=order, menu_item=menu_item, quantity=2, price=menu_item.price, workflow_state=served_state)

print(f"Created Order #{order.id} for Table T{table.number}")

# Step 2: Generate Bill & Release Table
factory = RequestFactory()
req_bill = factory.post(f'/hotel-pos/generate-bill/{order.id}/', {'apply_tax': 'on'})
req_bill.user = admin_user
generate_bill(req_bill, order.id)

req_release = factory.post(f'/hotel-pos/release-table/{order.id}/')
req_release.user = admin_user
setattr(req_release, 'session', {})
setattr(req_release, '_messages', FallbackStorage(req_release))
release_table(req_release, order.id)

order.refresh_from_db()
print(f"Order #{order.id} released. Status: {order.workflow_state.name}, Total: INR {order.total_amount}")
assert order.workflow_state.name == 'Closed', "Order should be Closed"

# Step 3: Verify Order appears in order_history view
req_history = factory.get('/hotel-pos/orders/')
req_history.user = admin_user
resp_history = order_history(req_history)
assert resp_history.status_code == 200, "Order history view should return 200"
assert f"#{order.id}" in resp_history.content.decode('utf-8'), "Released order must appear in rendered HTML"
print("SUCCESS: Order appears in order_history view.")

# Step 4: Verify Bill Reprinting on Closed Order
req_receipt = factory.get(f'/hotel-pos/receipt/{order.id}/')
req_receipt.user = admin_user
resp_receipt = receipt_printer(req_receipt, order.id)
assert resp_receipt.status_code == 200, "Receipt printer should return 200 for closed order"
print("SUCCESS: Receipt can be reprinted for released/closed order.")

# Step 5: Test Re-Opening Mistakenly Released Order
req_reopen = factory.post(f'/hotel-pos/reopen-order/{order.id}/')
req_reopen.user = admin_user
setattr(req_reopen, 'session', {})
setattr(req_reopen, '_messages', FallbackStorage(req_reopen))
resp_reopen = reopen_order(req_reopen, order.id)

order.refresh_from_db()
print(f"Order #{order.id} re-opened status: {order.workflow_state.name}")
assert order.workflow_state.name in ['Billed', 'Open'], "Order should be restored to Billed or Open"

# Check table is occupied again by this order
active_order = Order.objects.filter(table=table).exclude(workflow_state__name__in=['Closed', 'Paid']).first()
assert active_order.id == order.id, "Table should be re-occupied by the restored order"
print("SUCCESS: Mistakenly released order was successfully restored and re-occupied the table!")

print("\nALL ORDER HISTORY, REPRINT, AND RECOVERY TESTS PASSED!")
