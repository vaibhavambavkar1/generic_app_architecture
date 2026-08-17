from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from .models import Order, OrderItem, MenuItem, Table
from core.models import State
from hotel_core.models import HotelBranch
from django.views.decorators.http import require_POST
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

from django.contrib import messages

@require_POST
def add_table(request):
    number = request.POST.get('number', '').strip()
    capacity = request.POST.get('capacity', 4)
    branch = HotelBranch.objects.first()
    
    if branch and number:
        if Table.objects.filter(branch=branch, number__iexact=number, is_active=True).exists():
            messages.error(request, f"Table '{number}' already exists.")
        else:
            Table.objects.create(branch=branch, number=number, capacity=capacity)
            messages.success(request, f"Table '{number}' created successfully.")
        
    return redirect('hotel_pos:table_dashboard')

@require_POST
def edit_table(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    number = request.POST.get('number', '').strip()
    capacity = request.POST.get('capacity')
    
    if number and number.lower() != table.number.lower():
        if Table.objects.filter(branch=table.branch, number__iexact=number, is_active=True).exists():
            messages.error(request, f"Table '{number}' already exists.")
            return redirect('hotel_pos:table_dashboard')
        table.number = number
        
    if capacity:
        table.capacity = capacity
    
    table.save()
    messages.success(request, f"Table '{table.number}' updated successfully.")
    
    return redirect('hotel_pos:table_dashboard')

@require_POST
def delete_table(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    # Don't delete if there is an active order
    active_order = Order.objects.filter(
        table=table
    ).exclude(
        workflow_state__name__in=['Closed', 'Paid']
    ).first()
    
    if not active_order:
        table.is_active = False # Soft delete
        table.save()
        messages.success(request, f"Table '{table.number}' deleted successfully.")
    else:
        messages.error(request, f"Cannot delete Table '{table.number}' because it has an active order.")
        
    return redirect('hotel_pos:table_dashboard')

def pos_dashboard(request, table_id=None):
    """ HTMX powered POS dashboard """
    categories = [] # Would fetch from MenuCategory
    items = MenuItem.objects.filter(is_active=True).select_related('category').order_by('category__name', 'name')
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
    
    # Fetch the Pending state explicitly
    from core.models import State
    pending_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Pending').first()
    
    # Check if this item is already in the order in 'Pending' state
    order_item, created = OrderItem.objects.get_or_create(
        order=order, 
        menu_item=item,
        workflow_state=pending_state,
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
        
    response = render(request, 'hotel_pos/partials/order_items.html', {'order': order})
    response['HX-Trigger'] = json.dumps({'openReceipt': f"/hotel-pos/receipt/{order.id}/"})
    return response

def kitchen_display_system(request):
    """ Kitchen Display System (KDS) """
    active_kots = OrderItem.objects.filter(workflow_state__name='Cooking').order_by('id')
    return render(request, 'hotel_pos/kds.html', {'kots': active_kots})

def mark_item_served(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    served_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Served').first()
    
    if served_state:
        item.workflow_state = served_state
        item.save()
        
    return HttpResponse("") # Removes the item from KDS

def receipt_printer(request, order_id):
    """ View for Thermal Receipt Printer (PDF) """
    from django.template.loader import render_to_string
    try:
        from xhtml2pdf import pisa
    except ImportError:
        pisa = None
        
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    
    html = render_to_string('hotel_pos/receipt_printer.html', {'order': order, 'items': items})
    
    if pisa:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="receipt_{order.id}.pdf"'
        
        # Create PDF
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response
    
    # Fallback if xhtml2pdf is not installed
    return HttpResponse(html)

def cancel_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    order = item.order
    
    if item.workflow_state and item.workflow_state.name == 'Served':
        # Do nothing if item is already served
        return render(request, 'hotel_pos/partials/order_items.html', {'order': order})
        
    cancelled_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Cancelled').first()
    if cancelled_state:
        item.workflow_state = cancelled_state
        item.save()
        
        # update order total
        valid_items = order.items.exclude(workflow_state__name='Cancelled')
        order.total_amount = sum(i.total_price for i in valid_items)
        order.save()
        
    return render(request, 'hotel_pos/partials/order_items.html', {'order': order})

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    cancelled_state_order = State.objects.filter(workflow__name='Order Lifecycle', name='Cancelled').first()
    cancelled_state_item = State.objects.filter(workflow__name='Order Item Lifecycle', name='Cancelled').first()
    
    if cancelled_state_order:
        order.workflow_state = cancelled_state_order
        order.save()
        
    if cancelled_state_item:
        order.items.update(workflow_state=cancelled_state_item)
        
    response = HttpResponse()
    response['HX-Redirect'] = reverse('hotel_pos:table_dashboard')
    return response
