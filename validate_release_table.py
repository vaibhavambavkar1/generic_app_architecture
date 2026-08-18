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
from hotel_pos.views import generate_bill, release_table, table_dashboard

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

print("--- Step 1: Prepare Test Data ---")
branch = HotelBranch.objects.first()
if not branch:
    branch = HotelBranch.objects.create(name='Downtown Grand', code='DTG')

table, _ = Table.objects.get_or_create(branch=branch, number='TEST-99', defaults={'capacity': 4, 'is_active': True})
# Ensure any old orders on test table are cleaned up
Order.objects.filter(table=table).delete()

cat = MenuCategory.objects.filter(branch=branch).first()
if not cat:
    cat = MenuCategory.objects.create(branch=branch, name='Main')

menu_item1 = MenuItem.objects.filter(category=cat).first()
if not menu_item1:
    menu_item1 = MenuItem.objects.create(category=cat, name='Special Pizza', price=250.0)

# Configure a test tax if not exists
tax_cfg, _ = TaxConfiguration.objects.get_or_create(
    branch=branch,
    name='GST',
    defaults={'percentage': 5.0, 'is_active': True}
)

# Fetch lifecycle states
open_state = State.objects.filter(workflow__name='Order Lifecycle', name='Open').first()
billed_state = State.objects.filter(workflow__name='Order Lifecycle', name='Billed').first()
closed_state = State.objects.filter(workflow__name='Order Lifecycle', name='Closed').first()
served_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Served').first()

# Create a new active order on table
order = Order.objects.create(table=table, branch=branch, workflow_state=open_state)
item = OrderItem.objects.create(order=order, menu_item=menu_item1, quantity=2, price=menu_item1.price, workflow_state=served_state)

print(f"Created Order #{order.id} for Table T{table.number} with 2x {menu_item1.name} (Status: {item.workflow_state.name})")

# Step 2: Check Table is Occupied
active_order_check = Order.objects.filter(table=table).exclude(workflow_state__name__in=['Closed', 'Paid']).first()
assert active_order_check.id == order.id, "Table should be occupied by active order"
print("SUCCESS: Table is occupied.")

# Step 3: Generate Bill with Tax
factory = RequestFactory()
request = factory.post(f'/hotel-pos/generate-bill/{order.id}/', {'apply_tax': 'on'})
request.user = admin_user
response = generate_bill(request, order.id)

order.refresh_from_db()
print(f"Generated Bill for Order #{order.id}: Subtotal={order.subtotal}, Tax={order.tax_amount}, Total={order.total_amount}, State={order.workflow_state.name}")
assert order.workflow_state.name == 'Billed', "Order should be in Billed state"
assert order.total_amount > 0, "Order total amount should be calculated"

# Step 4: Call release_table
initial_audit_count = AuditLog.objects.filter(object_id=order.id).count()

req_release = factory.post(f'/hotel-pos/release-table/{order.id}/')
req_release.user = admin_user
# Add session and messages
setattr(req_release, 'session', {})
messages_storage = FallbackStorage(req_release)
setattr(req_release, '_messages', messages_storage)

release_resp = release_table(req_release, order.id)

order.refresh_from_db()
print(f"Order #{order.id} state after release: {order.workflow_state.name}")
assert order.workflow_state.name in ['Closed', 'Paid'], f"Order state should be Closed or Paid, got {order.workflow_state.name}"

# Step 5: Check Table is now FREE
freed_active_order = Order.objects.filter(table=table).exclude(workflow_state__name__in=['Closed', 'Paid']).first()
assert freed_active_order is None, "Table should now be Free with no active open/billed order"
print(f"SUCCESS: Table T{table.number} is now FREE!")

# Step 6: Verify Audit Logs
audit_log = AuditLog.objects.filter(object_id=order.id).order_by('-id').first()
assert audit_log is not None, "AuditLog entry should be recorded"
print(f"SUCCESS: AuditLog recorded -> Action: {audit_log.action}, Details: {audit_log.new_values}")

print("\nALL RELEASE TABLE & LOGGING TESTS PASSED SUCCESSFULLY!")
