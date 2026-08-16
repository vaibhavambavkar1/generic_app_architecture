from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from .models import Order, OrderItem, MenuItem, Table
from core.models import State
import json

def table_dashboard(request):
    """ View for Floor Staff to manage tables """
    # Fetch all tables and annotate if they have an active order
    tables = Table.objects.filter(is_active=True).order_by('number')
    
    table_data = []
    for table in tables:
        # Find an open order for this table
        # An order is active if its workflow state is not 'Closed' or 'Paid'
        active_order = Order.objects.filter(
            table=table
        ).exclude(
            workflow_state__name__in=['Closed', 'Paid']
        ).first()
        
        table_data.append({
            'table': table,
            'is_occupied': active_order is not None,
            'active_order': active_order,
        })
        
    return render(request, 'hotel_pos/table_dashboard.html', {'table_data': table_data})

def pos_dashboard(request, table_id=None):
    """ HTMX powered POS dashboard """
    categories = [] # Would fetch from MenuCategory
    items = MenuItem.objects.filter(is_active=True)
    tables = Table.objects.filter(is_active=True)
    
    active_order = None
    if table_id:
        table = get_object_or_404(Table, id=table_id)
        # Try to find an open order
        active_order = Order.objects.filter(
            table=table
        ).exclude(
            workflow_state__name__in=['Closed', 'Paid']
        ).first()
        
        # If no open order, create a new one
        if not active_order:
            # Need to get a branch. In a real app we get the user's current branch or shift.
            branch = table.branch
            active_order = Order.objects.create(table=table, branch=branch)
            # workflow state will be automatically assigned 'Open' by WorkflowMixin
            
    context = {
        'items': items,
        'tables': tables,
        'active_order': active_order,
    }
    return render(request, 'hotel_pos/pos_dashboard.html', context)

def add_to_order(request, order_id, item_id):
    """ HTMX endpoint to add item to current order """
    order = get_object_or_404(Order, id=order_id)
    item = get_object_or_404(MenuItem, id=item_id)
    
    # Check if this item is already in the order in 'Pending' state
    order_item, created = OrderItem.objects.get_or_create(
        order=order, 
        menu_item=item,
        workflow_state__name='Pending',
        defaults={'price': item.price, 'quantity': 1}
    )
    
    if not created:
        order_item.quantity += 1
        order_item.save()
        
    # Re-render the order items partial
    return render(request, 'hotel_pos/partials/order_items.html', {'order': order})

def send_to_kitchen(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    pending_items = order.items.filter(workflow_state__name='Pending')
    
    cooking_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Cooking').first()
    
    for item in pending_items:
        if cooking_state:
            item.workflow_state = cooking_state
            item.save()
            
    return render(request, 'hotel_pos/partials/order_items.html', {'order': order})

def generate_bill(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    billed_state = State.objects.filter(workflow__name='Order Lifecycle', name='Billed').first()
    
    if billed_state:
        order.workflow_state = billed_state
        
        # calculate total amount
        total = sum(i.total_price for i in order.items.all())
        order.total_amount = total
        order.save()
        
    return render(request, 'hotel_pos/partials/order_items.html', {'order': order})

def kitchen_display_system(request):
    """ Kitchen Display System (KDS) """
    active_kots = OrderItem.objects.filter(workflow_state__name='Cooking').order_by('created_at')
    return render(request, 'hotel_pos/kds.html', {'kots': active_kots})

def mark_item_served(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    served_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Served').first()
    
    if served_state:
        item.workflow_state = served_state
        item.save()
        
    return HttpResponse("") # Removes the item from KDS

def receipt_printer(request, order_id):
    """ View for Thermal Receipt Printer """
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    return render(request, 'hotel_pos/receipt_printer.html', {'order': order, 'items': items})
