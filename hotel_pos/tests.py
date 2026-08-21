import pytest
from decimal import Decimal
from datetime import timedelta
import json

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.contenttypes.models import ContentType

from core.models import Organization, Workflow, State, Transition, AuditLog
from hotel_core.models import HotelBranch
from hotel_pos.models import Table, MenuCategory, MenuItem, Order, OrderItem, TaxConfiguration

User = get_user_model()


@pytest.fixture(autouse=True)
def setup_pos_data(db):
    """
    Standard fixture to set up organization, branch, workflows, states, and user.
    """
    # 1. Organization & Branch
    org, _ = Organization.objects.get_or_create(
        name="Grand Test Hotel",
        defaults={"owner_name": "Admin", "email": "admin@grandhotel.com"}
    )
    branch, _ = HotelBranch.objects.get_or_create(
        name="Downtown Test Branch",
        defaults={"code": "DTG-TEST", "organization": org, "is_active": True}
    )

    # 2. Order Workflow
    order_wf, _ = Workflow.objects.get_or_create(
        name='Order Lifecycle',
        defaults={'model_name': 'hotel_pos.Order', 'description': 'Order lifecycle'}
    )
    o_open, _ = State.objects.get_or_create(workflow=order_wf, name='Open', defaults={'is_initial': True})
    o_billed, _ = State.objects.get_or_create(workflow=order_wf, name='Billed')
    o_paid, _ = State.objects.get_or_create(workflow=order_wf, name='Paid')
    o_closed, _ = State.objects.get_or_create(workflow=order_wf, name='Closed', defaults={'is_final': True})
    o_cancelled, _ = State.objects.get_or_create(workflow=order_wf, name='Cancelled', defaults={'is_final': True})

    # 3. OrderItem Workflow
    item_wf, _ = Workflow.objects.get_or_create(
        name='Order Item Lifecycle',
        defaults={'model_name': 'hotel_pos.OrderItem', 'description': 'Item lifecycle'}
    )
    i_pending, _ = State.objects.get_or_create(workflow=item_wf, name='Pending', defaults={'is_initial': True})
    i_cooking, _ = State.objects.get_or_create(workflow=item_wf, name='Cooking')
    i_served, _ = State.objects.get_or_create(workflow=item_wf, name='Served', defaults={'is_final': True})
    i_cancelled, _ = State.objects.get_or_create(workflow=item_wf, name='Cancelled', defaults={'is_final': True})

    # 4. User
    user, _ = User.objects.get_or_create(username="test_waiter", defaults={"is_staff": True})

    # 5. Tables
    t1, _ = Table.objects.get_or_create(branch=branch, number="1", defaults={"capacity": 4, "is_active": True})
    t2, _ = Table.objects.get_or_create(branch=branch, number="2", defaults={"capacity": 2, "is_active": True})

    # 6. Categories & Menu Items
    cat, _ = MenuCategory.objects.get_or_create(branch=branch, name="Main Course")
    m1, _ = MenuItem.objects.get_or_create(
        category=cat, name="Grilled Chicken",
        defaults={"price": Decimal("15.99"), "is_active": True}
    )
    m2, _ = MenuItem.objects.get_or_create(
        category=cat, name="Tomato Pasta",
        defaults={"price": Decimal("12.99"), "is_active": True}
    )

    return {
        "org": org,
        "branch": branch,
        "user": user,
        "table1": t1,
        "table2": t2,
        "item_chicken": m1,
        "item_pasta": m2,
        "states": {
            "order_open": o_open,
            "order_billed": o_billed,
            "order_paid": o_paid,
            "order_closed": o_closed,
            "order_cancelled": o_cancelled,
            "item_pending": i_pending,
            "item_cooking": i_cooking,
            "item_served": i_served,
            "item_cancelled": i_cancelled,
        }
    }


# ============================================================================
# 1. TABLE MANAGEMENT TESTS
# ============================================================================

@pytest.mark.django_db
def test_table_dashboard_metrics(client, setup_pos_data):
    """
    Validates table_dashboard view returns 200 and calculates floor metrics accurately.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    o_open = setup_pos_data["states"]["order_open"]

    # Table 1 is occupied
    Order.objects.create(table=t1, branch=branch, workflow_state=o_open)

    url = reverse("hotel_pos:table_dashboard")
    response = client.get(url)

    assert response.status_code == 200
    stats = response.context["stats"]
    assert stats["total_tables"] == 2
    assert stats["free_count"] == 1
    assert stats["occupied_count"] == 1
    assert stats["billed_count"] == 0
    assert stats["total_capacity"] == 6  # 4 + 2
    assert stats["occupied_capacity"] == 4


@pytest.mark.django_db
def test_add_table_success(client, setup_pos_data):
    """
    Validates adding a new table with valid number and capacity.
    """
    url = reverse("hotel_pos:add_table")
    response = client.post(url, {"number": "15", "capacity": "6"}, follow=True)

    assert response.status_code == 200
    created_table = Table.objects.filter(number="15", is_active=True).first()
    assert created_table is not None
    assert created_table.capacity == 6

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert any("Table '15' created successfully" in msg for msg in messages)


@pytest.mark.django_db
def test_add_table_duplicate_prevented(client, setup_pos_data):
    """
    Validates duplicate active table numbers are rejected.
    """
    url = reverse("hotel_pos:add_table")
    response = client.post(url, {"number": "1", "capacity": "4"}, follow=True)

    assert response.status_code == 200
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert any("Table '1' already exists" in msg for msg in messages)


@pytest.mark.django_db
def test_add_table_restore_inactive(client, setup_pos_data):
    """
    Validates that re-adding a soft-deleted table restores it with new capacity.
    """
    t1 = setup_pos_data["table1"]
    t1.is_active = False
    t1.save()

    url = reverse("hotel_pos:add_table")
    response = client.post(url, {"number": "1", "capacity": "8"}, follow=True)

    assert response.status_code == 200
    t1.refresh_from_db()
    assert t1.is_active is True
    assert t1.capacity == 8


@pytest.mark.django_db
def test_add_table_empty_number_error(client, setup_pos_data):
    """
    Validates that empty table numbers are rejected.
    """
    url = reverse("hotel_pos:add_table")
    response = client.post(url, {"number": "   ", "capacity": "4"}, follow=True)

    assert response.status_code == 200
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert any("Table number/name is required" in msg for msg in messages)


@pytest.mark.django_db
def test_edit_table_success(client, setup_pos_data):
    """
    Validates updating table number and capacity.
    """
    t1 = setup_pos_data["table1"]
    url = reverse("hotel_pos:edit_table", kwargs={"table_id": t1.id})
    response = client.post(url, {"number": "1-VIP", "capacity": "10"}, follow=True)

    assert response.status_code == 200
    t1.refresh_from_db()
    assert t1.number == "1-VIP"
    assert t1.capacity == 10


@pytest.mark.django_db
def test_edit_table_duplicate_conflict(client, setup_pos_data):
    """
    Validates editing table number to conflict with another active table is blocked.
    """
    t2 = setup_pos_data["table2"]  # number is '2'
    url = reverse("hotel_pos:edit_table", kwargs={"table_id": t2.id})
    response = client.post(url, {"number": "1", "capacity": "2"}, follow=True)

    assert response.status_code == 200
    t2.refresh_from_db()
    assert t2.number == "2"  # Unchanged
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert any("already exists" in msg for msg in messages)


@pytest.mark.django_db
def test_delete_table_success_when_free(client, setup_pos_data):
    """
    Validates deleting (soft delete) a table when it has no active order.
    """
    t1 = setup_pos_data["table1"]
    url = reverse("hotel_pos:delete_table", kwargs={"table_id": t1.id})
    response = client.post(url, follow=True)

    assert response.status_code == 200
    t1.refresh_from_db()
    assert t1.is_active is False


@pytest.mark.django_db
def test_delete_table_blocked_when_occupied(client, setup_pos_data):
    """
    Validates deleting a table is blocked when it has an active order.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    o_open = setup_pos_data["states"]["order_open"]

    Order.objects.create(table=t1, branch=branch, workflow_state=o_open)

    url = reverse("hotel_pos:delete_table", kwargs={"table_id": t1.id})
    response = client.post(url, follow=True)

    assert response.status_code == 200
    t1.refresh_from_db()
    assert t1.is_active is True  # Still active
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert any("Cannot delete" in msg for msg in messages)


# ============================================================================
# 2. POS DASHBOARD & ORDER MANAGEMENT TESTS
# ============================================================================

@pytest.mark.django_db
def test_pos_dashboard_without_table(client, setup_pos_data):
    """
    Validates POS dashboard renders cleanly without a selected table.
    """
    url = reverse("hotel_pos:pos_dashboard")
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["active_order"] is None
    assert len(response.context["items"]) == 2
    assert len(response.context["tables"]) == 2


@pytest.mark.django_db
def test_pos_dashboard_auto_creates_order_for_table(client, setup_pos_data):
    """
    Validates POS dashboard creates an Open Order if table is unoccupied.
    """
    t1 = setup_pos_data["table1"]
    url = reverse("hotel_pos:pos_dashboard_table", kwargs={"table_id": t1.id})
    response = client.get(url)

    assert response.status_code == 200
    active_order = response.context["active_order"]
    assert active_order is not None
    assert active_order.table == t1
    assert active_order.workflow_state.name == "Open"


# ============================================================================
# 3. ORDER ITEMS & KITCHEN LIFECYCLE TESTS
# ============================================================================

@pytest.mark.django_db
def test_add_to_order_and_quantity_increment(client, setup_pos_data):
    """
    Validates adding items to an order and incrementing quantity on subsequent clicks.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    o_open = setup_pos_data["states"]["order_open"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)

    url = reverse("hotel_pos:add_to_order", kwargs={"order_id": order.id, "item_id": m1.id})

    # First add
    res1 = client.get(url)
    assert res1.status_code == 200
    item_record = OrderItem.objects.get(order=order, menu_item=m1)
    assert item_record.quantity == 1
    assert item_record.workflow_state.name == "Pending"

    # Second add (increments)
    res2 = client.get(url)
    assert res2.status_code == 200
    item_record.refresh_from_db()
    assert item_record.quantity == 2


@pytest.mark.django_db
def test_send_to_kitchen(client, setup_pos_data):
    """
    Validates send_to_kitchen transitions all Pending items to Cooking.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    m2 = setup_pos_data["item_pasta"]
    o_open = setup_pos_data["states"]["order_open"]
    i_pending = setup_pos_data["states"]["item_pending"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    item1 = OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_pending)
    item2 = OrderItem.objects.create(order=order, menu_item=m2, quantity=2, price=m2.price, workflow_state=i_pending)

    url = reverse("hotel_pos:send_to_kitchen", kwargs={"order_id": order.id})
    response = client.get(url)

    assert response.status_code == 200
    item1.refresh_from_db()
    item2.refresh_from_db()
    assert item1.workflow_state.name == "Cooking"
    assert item2.workflow_state.name == "Cooking"


@pytest.mark.django_db
def test_mark_item_served(client, setup_pos_data):
    """
    Validates mark_item_served transitions an individual item from Cooking to Served.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    o_open = setup_pos_data["states"]["order_open"]
    i_cooking = setup_pos_data["states"]["item_cooking"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    item = OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_cooking)

    url = reverse("hotel_pos:mark_item_served", kwargs={"item_id": item.id})
    response = client.post(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.workflow_state.name == "Served"


@pytest.mark.django_db
def test_bump_kot_ticket(client, setup_pos_data):
    """
    Validates bump_kot_ticket marks all Cooking items for an entire order as Served.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    m2 = setup_pos_data["item_pasta"]
    o_open = setup_pos_data["states"]["order_open"]
    i_cooking = setup_pos_data["states"]["item_cooking"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    item1 = OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_cooking)
    item2 = OrderItem.objects.create(order=order, menu_item=m2, quantity=2, price=m2.price, workflow_state=i_cooking)

    url = reverse("hotel_pos:bump_kot_ticket", kwargs={"order_id": order.id})
    response = client.post(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    item1.refresh_from_db()
    item2.refresh_from_db()
    assert item1.workflow_state.name == "Served"
    assert item2.workflow_state.name == "Served"


@pytest.mark.django_db
def test_cancel_item_unserved(client, setup_pos_data):
    """
    Validates cancelling a Pending or Cooking item updates state and order total.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    o_open = setup_pos_data["states"]["order_open"]
    i_cooking = setup_pos_data["states"]["item_cooking"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    item = OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_cooking)

    url = reverse("hotel_pos:cancel_item", kwargs={"item_id": item.id})
    response = client.get(url)

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.workflow_state.name == "Cancelled"
    order.refresh_from_db()
    assert order.total_amount == Decimal("0.00")


@pytest.mark.django_db
def test_cancel_item_served_blocked(client, setup_pos_data):
    """
    Validates that an item with status 'Served' cannot be cancelled.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    o_open = setup_pos_data["states"]["order_open"]
    i_served = setup_pos_data["states"]["item_served"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    item = OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_served)

    url = reverse("hotel_pos:cancel_item", kwargs={"item_id": item.id})
    response = client.get(url)

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.workflow_state.name == "Served"  # Remains Served


@pytest.mark.django_db
def test_cancel_order(client, setup_pos_data):
    """
    Validates cancel_order marks order and all items as Cancelled.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    o_open = setup_pos_data["states"]["order_open"]
    i_pending = setup_pos_data["states"]["item_pending"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    item = OrderItem.objects.create(order=order, menu_item=m1, quantity=2, price=m1.price, workflow_state=i_pending)

    url = reverse("hotel_pos:cancel_order", kwargs={"order_id": order.id})
    response = client.post(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert response["HX-Redirect"] == reverse("hotel_pos:table_dashboard")

    order.refresh_from_db()
    item.refresh_from_db()
    assert order.workflow_state.name == "Cancelled"
    assert item.workflow_state.name == "Cancelled"

    # Verify table is now released and free in table dashboard
    t_dash_res = client.get(reverse("hotel_pos:table_dashboard"))
    assert t_dash_res.status_code == 200
    # In table_dashboard, free_count should count table1 as available
    assert t_dash_res.context["stats"]["free_count"] >= 1

    # Verify opening POS for table1 creates a brand new Open order (not reusing the cancelled one)
    pos_res = client.get(reverse("hotel_pos:pos_dashboard_table", kwargs={"table_id": t1.id}))
    assert pos_res.status_code == 200
    new_order = pos_res.context["active_order"]
    assert new_order is not None
    assert new_order.id != order.id
    assert new_order.workflow_state.name == "Open"

    # Verify AuditLog created
    ct = ContentType.objects.get_for_model(Order)
    log = AuditLog.objects.filter(content_type=ct, object_id=order.id).first()
    assert log is not None
    assert log.new_values["event"] == "ORDER_CANCELLED_AND_TABLE_RELEASED"
    assert log.new_values["status"] == "Released"


# ============================================================================
# 4. KITCHEN DISPLAY SYSTEM (KDS) TESTS
# ============================================================================

@pytest.mark.django_db
def test_kitchen_display_system_view(client, setup_pos_data):
    """
    Validates KDS view renders active cooking tickets, batch summary, and wait timers.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    m2 = setup_pos_data["item_pasta"]
    o_open = setup_pos_data["states"]["order_open"]
    i_cooking = setup_pos_data["states"]["item_cooking"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    OrderItem.objects.create(order=order, menu_item=m1, quantity=3, price=m1.price, workflow_state=i_cooking)
    OrderItem.objects.create(order=order, menu_item=m2, quantity=1, price=m2.price, workflow_state=i_cooking)

    url = reverse("hotel_pos:kds")
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.context["tickets"]) == 1
    ticket = response.context["tickets"][0]
    assert ticket["order"] == order
    assert ticket["total_qty"] == 4
    assert ticket["urgency"] == "normal"

    # Batch summary
    prep_summary = response.context["prep_summary"]
    assert len(prep_summary) == 2


# ============================================================================
# 5. BILL GENERATION, TAX & RECEIPT TESTS
# ============================================================================

@pytest.mark.django_db
def test_generate_bill_served_items_only_without_tax(client, setup_pos_data):
    """
    Validates generate_bill includes ONLY Served items and sets order to Billed.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]  # 15.99
    m2 = setup_pos_data["item_pasta"]    # 12.99
    o_open = setup_pos_data["states"]["order_open"]
    i_served = setup_pos_data["states"]["item_served"]
    i_cancelled = setup_pos_data["states"]["item_cancelled"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    # Served item: 2 x 15.99 = 31.98
    OrderItem.objects.create(order=order, menu_item=m1, quantity=2, price=m1.price, workflow_state=i_served)
    # Cancelled item: Should NOT be in total
    OrderItem.objects.create(order=order, menu_item=m2, quantity=1, price=m2.price, workflow_state=i_cancelled)

    url = reverse("hotel_pos:generate_bill", kwargs={"order_id": order.id})
    response = client.post(url, {})

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.workflow_state.name == "Billed"
    assert order.tax_amount == Decimal("0.00")
    assert order.total_amount == Decimal("31.98")
    assert "openReceipt" in response["HX-Trigger"]


@pytest.mark.django_db
def test_generate_bill_with_configured_tax(client, setup_pos_data):
    """
    Validates generate_bill applies active TaxConfiguration percentage with Decimal precision.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]  # 15.99
    o_open = setup_pos_data["states"]["order_open"]
    i_served = setup_pos_data["states"]["item_served"]

    # 5% GST
    TaxConfiguration.objects.create(branch=branch, name="GST", percentage=Decimal("5.00"), is_active=True)

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    OrderItem.objects.create(order=order, menu_item=m1, quantity=2, price=m1.price, workflow_state=i_served)

    url = reverse("hotel_pos:generate_bill", kwargs={"order_id": order.id})
    response = client.post(url, {"apply_tax": "on"})

    assert response.status_code == 200
    order.refresh_from_db()
    expected_subtotal = Decimal("31.98")
    expected_tax = (expected_subtotal * Decimal("0.05")).quantize(Decimal("0.01"))  # 1.60
    expected_total = expected_subtotal + expected_tax  # 33.58

    assert order.tax_amount == expected_tax
    assert order.total_amount == expected_total
    assert order.is_tax_applied is True


@pytest.mark.django_db
def test_receipt_printer_view(client, setup_pos_data):
    """
    Validates thermal receipt printer view generates receipt for Served items.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    o_billed = setup_pos_data["states"]["order_billed"]
    i_served = setup_pos_data["states"]["item_served"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_billed, total_amount=Decimal("15.99"))
    OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_served)

    url = reverse("hotel_pos:receipt_printer", kwargs={"order_id": order.id})
    response = client.get(url)

    assert response.status_code == 200
    assert response.has_header("Content-Type")


# ============================================================================
# 6. TABLE RELEASE & AUDIT LOGGING TESTS
# ============================================================================

@pytest.mark.django_db
def test_release_table_lifecycle_and_audit(client, setup_pos_data):
    """
    Validates release_table transitions order to Closed, logs AuditLog, and frees table.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    user = setup_pos_data["user"]
    o_billed = setup_pos_data["states"]["order_billed"]
    i_served = setup_pos_data["states"]["item_served"]

    order = Order.objects.create(
        table=t1, branch=branch, workflow_state=o_billed,
        total_amount=Decimal("15.99"), waiter=user
    )
    OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_served)

    client.force_login(user)
    url = reverse("hotel_pos:release_table", kwargs={"order_id": order.id})
    response = client.post(url, follow=True)

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.workflow_state.name == "Closed"

    # Verify AuditLog created
    ct = ContentType.objects.get_for_model(Order)
    log = AuditLog.objects.filter(content_type=ct, object_id=order.id).first()
    assert log is not None
    assert log.new_values["event"] == "ORDER_COMPLETED_AND_TABLE_RELEASED"
    assert log.new_values["workflow_state"] == "Closed"
    assert log.new_values["table_number"] == "1"


@pytest.mark.django_db
def test_table_workflow_disallows_bill_and_release_when_cooking_and_pending(client, setup_pos_data):
    """
    Scenario: Table has items in Cooking and Pending states.
    Requirement: Disallow generate_bill and release_table.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    m2 = setup_pos_data["item_pasta"]
    o_open = setup_pos_data["states"]["order_open"]
    i_pending = setup_pos_data["states"]["item_pending"]
    i_cooking = setup_pos_data["states"]["item_cooking"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_pending)
    OrderItem.objects.create(order=order, menu_item=m2, quantity=1, price=m2.price, workflow_state=i_cooking)

    assert order.has_unserved_items is True
    assert order.can_generate_bill_and_release is False

    # Attempt Generate Bill
    bill_url = reverse("hotel_pos:generate_bill", kwargs={"order_id": order.id})
    client.post(bill_url, {})
    order.refresh_from_db()
    assert order.workflow_state.name == "Open"  # Remains Open, NOT Billed

    # Attempt Release Table
    release_url = reverse("hotel_pos:release_table", kwargs={"order_id": order.id})
    client.post(release_url, {})
    order.refresh_from_db()
    assert order.workflow_state.name == "Open"  # Remains Open, NOT Closed


@pytest.mark.django_db
def test_table_workflow_disallows_bill_and_release_when_served_and_pending(client, setup_pos_data):
    """
    Scenario: Table has items in Served and Pending states.
    Requirement: Disallow generate_bill and release_table.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    m2 = setup_pos_data["item_pasta"]
    o_open = setup_pos_data["states"]["order_open"]
    i_served = setup_pos_data["states"]["item_served"]
    i_pending = setup_pos_data["states"]["item_pending"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_served)
    OrderItem.objects.create(order=order, menu_item=m2, quantity=1, price=m2.price, workflow_state=i_pending)

    assert order.has_unserved_items is True
    assert order.can_generate_bill_and_release is False

    # Attempt Generate Bill -> Blocked
    bill_url = reverse("hotel_pos:generate_bill", kwargs={"order_id": order.id})
    client.post(bill_url, {})
    order.refresh_from_db()
    assert order.workflow_state.name == "Open"

    # Attempt Release Table -> Blocked
    release_url = reverse("hotel_pos:release_table", kwargs={"order_id": order.id})
    client.post(release_url, {})
    order.refresh_from_db()
    assert order.workflow_state.name == "Open"


@pytest.mark.django_db
def test_table_workflow_disallows_bill_and_release_when_served_and_cooking(client, setup_pos_data):
    """
    Scenario: Table has items in Served and Cooking states.
    Requirement: Disallow generate_bill and release_table.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    m2 = setup_pos_data["item_pasta"]
    o_open = setup_pos_data["states"]["order_open"]
    i_served = setup_pos_data["states"]["item_served"]
    i_cooking = setup_pos_data["states"]["item_cooking"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_served)
    OrderItem.objects.create(order=order, menu_item=m2, quantity=1, price=m2.price, workflow_state=i_cooking)

    assert order.has_unserved_items is True
    assert order.can_generate_bill_and_release is False

    # Attempt Generate Bill -> Blocked
    bill_url = reverse("hotel_pos:generate_bill", kwargs={"order_id": order.id})
    client.post(bill_url, {})
    order.refresh_from_db()
    assert order.workflow_state.name == "Open"

    # Attempt Release Table -> Blocked
    release_url = reverse("hotel_pos:release_table", kwargs={"order_id": order.id})
    client.post(release_url, {})
    order.refresh_from_db()
    assert order.workflow_state.name == "Open"


@pytest.mark.django_db
def test_table_workflow_allows_bill_and_release_when_all_items_served(client, setup_pos_data):
    """
    Scenario: Table has order items and ALL are in Served state.
    Requirement: Allow generate_bill and release_table.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    m1 = setup_pos_data["item_chicken"]
    m2 = setup_pos_data["item_pasta"]
    o_open = setup_pos_data["states"]["order_open"]
    i_served = setup_pos_data["states"]["item_served"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_open)
    OrderItem.objects.create(order=order, menu_item=m1, quantity=1, price=m1.price, workflow_state=i_served)
    OrderItem.objects.create(order=order, menu_item=m2, quantity=2, price=m2.price, workflow_state=i_served)

    assert order.has_unserved_items is False
    assert order.can_generate_bill_and_release is True

    # 1. Generate Bill succeeds
    bill_url = reverse("hotel_pos:generate_bill", kwargs={"order_id": order.id})
    bill_res = client.post(bill_url, {})
    assert bill_res.status_code == 200
    order.refresh_from_db()
    assert order.workflow_state.name == "Billed"
    assert order.total_amount == Decimal("41.97")  # 15.99 + 2*12.99

    # 2. Release Table succeeds
    release_url = reverse("hotel_pos:release_table", kwargs={"order_id": order.id})
    release_res = client.post(release_url, follow=True)
    assert release_res.status_code == 200
    order.refresh_from_db()
    assert order.workflow_state.name == "Closed"



# ============================================================================
# 7. BILLS & ORDER HISTORY DASHBOARD TESTS
# ============================================================================

@pytest.mark.django_db
def test_order_history_pagination_and_filters(client, setup_pos_data):
    """
    Validates order_history dashboard has 10 records per page pagination, search, and status filters.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    o_closed = setup_pos_data["states"]["order_closed"]

    # Create 15 closed orders
    for i in range(15):
        Order.objects.create(
            table=t1, branch=branch, workflow_state=o_closed,
            total_amount=Decimal("50.00"), customer_name=f"Customer {i+1}"
        )

    url = reverse("hotel_pos:order_history")

    # Page 1: Exactly 10 records
    res_p1 = client.get(url, {"page": "1"})
    assert res_p1.status_code == 200
    assert len(res_p1.context["orders"]) == 10
    assert res_p1.context["stats"]["completed_count"] == 15
    assert res_p1.context["stats"]["total_revenue"] == Decimal("750.00")

    # Page 2: Remaining 5 records
    res_p2 = client.get(url, {"page": "2"})
    assert res_p2.status_code == 200
    assert len(res_p2.context["orders"]) == 5

    # Search filter by customer name
    res_search = client.get(url, {"q": "Customer 12"})
    assert res_search.status_code == 200
    assert len(res_search.context["orders"]) == 1

    # Status filter
    res_filter = client.get(url, {"status": "completed"})
    assert res_filter.status_code == 200
    assert res_filter.context["total_count"] == 15


# ============================================================================
# 8. ORDER RECOVERY / REOPENING TESTS
# ============================================================================

@pytest.mark.django_db
def test_reopen_order_success(client, setup_pos_data):
    """
    Validates reopening a Closed order restores it to Billed/Open and logs audit entry.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    user = setup_pos_data["user"]
    o_closed = setup_pos_data["states"]["order_closed"]

    order = Order.objects.create(table=t1, branch=branch, workflow_state=o_closed, total_amount=Decimal("20.00"))

    client.force_login(user)
    url = reverse("hotel_pos:reopen_order", kwargs={"order_id": order.id})
    response = client.post(url, follow=True)

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.workflow_state.name in ["Billed", "Open"]

    # Verify AuditLog created for recovery
    ct = ContentType.objects.get_for_model(Order)
    log = AuditLog.objects.filter(content_type=ct, object_id=order.id, new_values__event="ORDER_REOPENED_AFTER_ACCIDENTAL_RELEASE").first()
    assert log is not None


@pytest.mark.django_db
def test_reopen_order_blocked_when_table_occupied(client, setup_pos_data):
    """
    Validates reopening an order is blocked if another active order is occupying the table.
    """
    branch = setup_pos_data["branch"]
    t1 = setup_pos_data["table1"]
    o_open = setup_pos_data["states"]["order_open"]
    o_closed = setup_pos_data["states"]["order_closed"]

    # Old closed order
    old_order = Order.objects.create(table=t1, branch=branch, workflow_state=o_closed, total_amount=Decimal("20.00"))

    # Current new active order on Table 1
    Order.objects.create(table=t1, branch=branch, workflow_state=o_open, total_amount=Decimal("10.00"))

    url = reverse("hotel_pos:reopen_order", kwargs={"order_id": old_order.id})
    response = client.post(url, follow=True)

    assert response.status_code == 200
    old_order.refresh_from_db()
    assert old_order.workflow_state.name == "Closed"  # Stays Closed
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert any("currently has active Order" in msg for msg in messages)
