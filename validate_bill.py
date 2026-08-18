import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_framework.settings')
django.setup()

from hotel_core.models import HotelBranch
from hotel_pos.models import Table, MenuItem, Order, OrderItem, MenuCategory
from core.models import State, Workflow
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

# Get states
pending_state = State.objects.filter(name='Pending').first()
cooking_state = State.objects.filter(name='Cooking').first()
served_state = State.objects.filter(name='Served').first()
cancelled_state = State.objects.filter(name='Cancelled').first()

branch = HotelBranch.objects.first()
if not branch:
    branch = HotelBranch.objects.create(name='Test Branch', code='TB01')

table = Table.objects.filter(branch=branch).first()
if not table:
    table = Table.objects.create(branch=branch, number='T1', capacity=4)

cat = MenuCategory.objects.filter(branch=branch).first()
if not cat:
    cat = MenuCategory.objects.create(branch=branch, name='Test Cat')

menu_item1 = MenuItem.objects.filter(category=cat).first()
if not menu_item1:
    menu_item1 = MenuItem.objects.create(category=cat, name='Served Item', price=100.0)

menu_item2 = MenuItem.objects.filter(category=cat).last()
if not menu_item2 or menu_item2 == menu_item1:
    menu_item2 = MenuItem.objects.create(category=cat, name='Cancelled Item', price=50.0)

# Create order
order = Order.objects.create(table=table, branch=branch)

# Add items
item1 = OrderItem.objects.create(order=order, menu_item=menu_item1, quantity=2, price=100.0)
item1.workflow_state = served_state
item1.save()

item2 = OrderItem.objects.create(order=order, menu_item=menu_item2, quantity=1, price=50.0)
item2.workflow_state = cancelled_state
item2.save()

item3 = OrderItem.objects.create(order=order, menu_item=menu_item2, quantity=1, price=50.0)
item3.workflow_state = pending_state
item3.save()

print(f"Items in order: {order.items.count()}")
print(f"Served Item total should be: 200.0")

# Simulate generate_bill
from django.test import RequestFactory
import sys
sys.modules['xhtml2pdf'] = None # Force fallback to HTML for testing
from hotel_pos.views import generate_bill, receipt_printer

factory = RequestFactory()
request = factory.post(f'/hotel-pos/generate-bill/{order.id}/')
request.user = admin_user

response = generate_bill(request, order.id)

order.refresh_from_db()
print(f"Calculated Order Total: {order.total_amount}")
if float(order.total_amount) == 200.0:
    print("SUCCESS: Total amount only includes Served items.")
else:
    print("ERROR: Total amount is incorrect.")

# Simulate receipt_printer
request = factory.get(f'/hotel-pos/receipt/{order.id}/')
request.user = admin_user
receipt_response = receipt_printer(request, order.id)

html_content = receipt_response.content.decode('utf-8')
if "Served Item" in html_content and "Cancelled Item" not in html_content:
    print("SUCCESS: Receipt HTML only includes Served item.")
else:
    print("ERROR: Receipt HTML contains incorrect items.")
    if "Cancelled Item" in html_content:
        print(" -> Contains Cancelled Item")
    if "Served Item" not in html_content:
        print(" -> Missing Served Item")
        print("--- HTML CONTENT ---")
        print(html_content)
        print("--------------------")
