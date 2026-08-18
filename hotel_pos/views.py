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
    tables = Table.objects.filter(is_active=True).order_by('number')
    
    table_data = []
    free_count = 0
    occupied_count = 0
    billed_count = 0
    total_capacity = 0
    occupied_capacity = 0
    
    for table in tables:
        total_capacity += table.capacity
        active_order = Order.objects.filter(
            table=table
        ).exclude(
            workflow_state__name__in=['Closed', 'Paid']
        ).select_related('workflow_state', 'waiter').prefetch_related('items__menu_item').first()
        
        is_occupied = active_order is not None
        order_status = active_order.workflow_state.name if (active_order and active_order.workflow_state) else ('Open' if is_occupied else 'Free')
        
        if is_occupied:
            occupied_count += 1
            occupied_capacity += table.capacity
            if order_status == 'Billed':
                billed_count += 1
        else:
            free_count += 1
            
        table_data.append({
            'table': table,
            'is_occupied': is_occupied,
            'order_status': order_status,
            'active_order': active_order,
        })
        
    context = {
        'table_data': table_data,
        'stats': {
            'total_tables': len(tables),
            'free_count': free_count,
            'occupied_count': occupied_count,
            'billed_count': billed_count,
            'total_capacity': total_capacity,
            'occupied_capacity': occupied_capacity,
        }
    }
    return render(request, 'hotel_pos/table_dashboard.html', context)

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
    if request.method == 'POST':
        billed_state = State.objects.filter(workflow__name='Order Lifecycle', name='Billed').first()
        if billed_state:
            order.workflow_state = billed_state
        
        # calculate total amount
        valid_items = order.items.filter(workflow_state__name='Served')
        total = sum(i.total_price for i in valid_items)
        
        apply_tax = request.POST.get('apply_tax') == 'on'
        tax_amount = 0
        if apply_tax:
            from .models import TaxConfiguration
            taxes = TaxConfiguration.objects.filter(branch=order.branch, is_active=True)
            total_tax_percentage = sum(t.percentage for t in taxes)
            tax_amount = total * (total_tax_percentage / 100)
            
        order.tax_amount = tax_amount
        order.total_amount = total + tax_amount
        order.is_tax_applied = apply_tax
        order.save()
        
    response = render(request, 'hotel_pos/partials/order_items.html', {'order': order})
    response['HX-Trigger'] = json.dumps({'openReceipt': f"/hotel-pos/receipt/{order.id}/"})
    return response

def kitchen_display_system(request):
    """
    Advanced Kitchen Display System (KDS):
    - Groups cooking items into KOT Order Tickets (by Table & Order)
    - Provides aggregated prep item summary counts
    - Tracks elapsed wait times with color-coded urgency
    - Supports station filtering and ticket bumping
    """
    from django.db.models import Sum, Count
    from django.utils import timezone
    now = timezone.now()
    
    # 1. Orders with items currently cooking
    active_orders = Order.objects.filter(
        items__workflow_state__name='Cooking'
    ).distinct().select_related('table', 'waiter', 'branch').prefetch_related(
        'items__menu_item__category', 'items__workflow_state'
    ).order_by('created_at')
    
    tickets = []
    total_cooking_items = 0
    
    for order in active_orders:
        cooking_items = order.items.filter(workflow_state__name='Cooking').select_related('menu_item')
        if cooking_items.exists():
            order_qty = sum(item.quantity for item in cooking_items)
            total_cooking_items += order_qty
            
            # Calculate elapsed minutes
            elapsed_seconds = (now - order.created_at).total_seconds()
            elapsed_minutes = int(elapsed_seconds // 60)
            
            # Urgency level: normal (<10m), warning (10-20m), urgent (>20m)
            if elapsed_minutes < 10:
                urgency = 'normal'
            elif elapsed_minutes < 20:
                urgency = 'warning'
            else:
                urgency = 'urgent'
                
            tickets.append({
                'order': order,
                'items': cooking_items,
                'items_count': cooking_items.count(),
                'total_qty': order_qty,
                'elapsed_minutes': elapsed_minutes,
                'urgency': urgency,
            })
            
    # 2. Aggregated preparation summary by dish
    prep_summary = OrderItem.objects.filter(
        workflow_state__name='Cooking'
    ).values('menu_item__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')
    
    # 3. Items served today
    served_today_count = OrderItem.objects.filter(
        workflow_state__name='Served',
        order__created_at__date=now.date()
    ).count()
    
    context = {
        'tickets': tickets,
        'prep_summary': prep_summary,
        'stats': {
            'active_tickets_count': len(tickets),
            'total_cooking_items': total_cooking_items,
            'served_today_count': served_today_count,
        }
    }
    return render(request, 'hotel_pos/kds.html', context)

@require_POST
def mark_item_served(request, item_id):
    """ Mark individual KOT item as Served """
    item = get_object_or_404(OrderItem, id=item_id)
    served_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Served').first()
    
    if served_state:
        item.workflow_state = served_state
        item.save()
        
    if request.headers.get('HX-Request'):
        return HttpResponse("")
    return redirect('hotel_pos:kds')

@require_POST
def bump_kot_ticket(request, order_id):
    """ Mark all cooking items for a table order as Served (Bump Ticket) """
    order = get_object_or_404(Order, id=order_id)
    served_state = State.objects.filter(workflow__name='Order Item Lifecycle', name='Served').first()
    
    if served_state:
        order.items.filter(workflow_state__name='Cooking').update(workflow_state=served_state)
        
    if request.headers.get('HX-Request'):
        return HttpResponse("")
    return redirect('hotel_pos:kds')

def receipt_printer(request, order_id):
    """ View for Thermal Receipt Printer (PDF) """
    from django.template.loader import render_to_string
    try:
        from xhtml2pdf import pisa
    except ImportError:
        pisa = None
        
    order = get_object_or_404(Order, id=order_id)
    items = order.items.filter(workflow_state__name='Served')
    
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

import logging
logger = logging.getLogger(__name__)

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

@require_POST
def release_table(request, order_id):
    """
    Complete order processing, finalize bill, record audit logs, and release the table.
    """
    from django.contrib.contenttypes.models import ContentType
    from core.models import AuditLog

    order = get_object_or_404(Order, id=order_id)
    table_number = order.table.number if order.table else "N/A"
    
    # 1. Finalize totals from served items if not already computed
    valid_items = order.items.filter(workflow_state__name='Served')
    subtotal = sum(i.total_price for i in valid_items)
    
    if order.total_amount == 0 and subtotal > 0:
        if order.is_tax_applied:
            from .models import TaxConfiguration
            taxes = TaxConfiguration.objects.filter(branch=order.branch, is_active=True)
            total_tax_percentage = sum(t.percentage for t in taxes)
            tax_amount = subtotal * (total_tax_percentage / 100)
            order.tax_amount = tax_amount
            order.total_amount = subtotal + tax_amount
        else:
            order.total_amount = subtotal
            
    # 2. Transition order to Closed state
    closed_state = State.objects.filter(workflow__name='Order Lifecycle', name='Closed').first()
    if not closed_state:
        closed_state = State.objects.filter(workflow__name='Order Lifecycle', name='Paid').first()
        
    old_state_name = order.workflow_state.name if order.workflow_state else 'Open'
    if closed_state:
        order.workflow_state = closed_state
        
    if request.user.is_authenticated:
        order._audit_user_id = request.user.id
        
    order.save()
    
    # 3. Compile audit trail details
    items_summary = [
        {
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'unit_price': str(item.price),
            'total_price': str(item.total_price),
            'status': item.workflow_state.name if item.workflow_state else 'Unknown'
        }
        for item in order.items.all()
    ]
    
    # Write to AuditLog
    content_type = ContentType.objects.get_for_model(Order)
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action='UPDATE',
        content_type=content_type,
        object_id=order.id,
        old_values={
            'workflow_state': old_state_name,
            'table_number': table_number,
            'status': 'Occupied'
        },
        new_values={
            'event': 'ORDER_COMPLETED_AND_TABLE_RELEASED',
            'workflow_state': 'Closed',
            'table_number': table_number,
            'subtotal': str(order.subtotal),
            'tax_amount': str(order.tax_amount),
            'total_amount': str(order.total_amount),
            'items_count': order.items.count(),
            'served_items_count': valid_items.count(),
            'items': items_summary
        }
    )
    
    logger.info(
        f"[ORDER COMPLETED & TABLE RELEASED] Order #{order.id} for Table T{table_number} released by {request.user}. "
        f"Subtotal: INR {order.subtotal}, Tax: INR {order.tax_amount}, Total: INR {order.total_amount}"
    )
    
    messages.success(request, f"Table T{table_number} released successfully. Order #{order.id} marked as completed.")
    
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Redirect'] = reverse('hotel_pos:table_dashboard')
        return response
        
    return redirect('hotel_pos:table_dashboard')

from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone

def order_history(request):
    """
    View to list all orders (past and active), with filtering, searching,
    reprinting bills, and viewing detailed order breakdowns.
    """
    now = timezone.now()
    all_orders = Order.objects.all()
    today_orders = all_orders.filter(created_at__date=now.date())
    
    total_revenue = all_orders.filter(workflow_state__name__in=['Closed', 'Paid', 'Billed']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    today_revenue = today_orders.filter(workflow_state__name__in=['Closed', 'Paid', 'Billed']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    completed_count = all_orders.filter(workflow_state__name__in=['Closed', 'Paid']).count()
    active_count = all_orders.exclude(workflow_state__name__in=['Closed', 'Paid', 'Cancelled']).count()
    
    orders_qs = Order.objects.select_related('table', 'branch', 'waiter', 'workflow_state').prefetch_related('items__menu_item', 'items__workflow_state').order_by('-created_at')
    
    # 1. Search Query (Order ID, Table Number, Customer Name)
    q = request.GET.get('q', '').strip()
    if q:
        query_filter = Q(customer_name__icontains=q) | Q(table__number__icontains=q)
        if q.isdigit():
            query_filter |= Q(id=int(q))
        elif q.lower().startswith('t') and q[1:].isdigit():
            query_filter |= Q(table__number=q[1:])
        orders_qs = orders_qs.filter(query_filter)
        
    # 2. Status Filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        if status_filter == 'active':
            orders_qs = orders_qs.exclude(workflow_state__name__in=['Closed', 'Paid', 'Cancelled'])
        elif status_filter == 'completed':
            orders_qs = orders_qs.filter(workflow_state__name__in=['Closed', 'Paid'])
        else:
            orders_qs = orders_qs.filter(workflow_state__name__iexact=status_filter)
            
    # 3. Date Filter
    date_filter = request.GET.get('date', 'all')
    if date_filter == 'today':
        orders_qs = orders_qs.filter(created_at__date=now.date())
    elif date_filter == 'week':
        orders_qs = orders_qs.filter(created_at__gte=now - timezone.timedelta(days=7))
        
    # Pagination: 10 records per page
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'q': q,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'total_count': paginator.count,
        'stats': {
            'total_revenue': total_revenue,
            'today_revenue': today_revenue,
            'completed_count': completed_count,
            'active_count': active_count,
            'total_orders': all_orders.count(),
        }
    }
    return render(request, 'hotel_pos/order_history.html', context)

@require_POST
def reopen_order(request, order_id):
    """
    Recovers an accidentally closed/released order and restores it on the table if available.
    """
    from django.contrib.contenttypes.models import ContentType
    from core.models import AuditLog

    order = get_object_or_404(Order, id=order_id)
    table = order.table
    
    if table:
        # Check if table has another active order
        existing_active = Order.objects.filter(table=table).exclude(
            id=order.id
        ).exclude(
            workflow_state__name__in=['Closed', 'Paid', 'Cancelled']
        ).first()
        
        if existing_active:
            messages.error(request, f"Cannot re-open Order #{order.id} on Table T{table.number} because Table T{table.number} currently has active Order #{existing_active.id}. Please clear that order first.")
            return redirect('hotel_pos:order_history')
            
    # Set back to Billed or Open state
    billed_state = State.objects.filter(workflow__name='Order Lifecycle', name='Billed').first()
    open_state = State.objects.filter(workflow__name='Order Lifecycle', name='Open').first()
    target_state = billed_state or open_state
    
    old_state_name = order.workflow_state.name if order.workflow_state else 'Closed'
    if target_state:
        order.workflow_state = target_state
        
    if request.user.is_authenticated:
        order._audit_user_id = request.user.id
    order.save()
    
    # Audit log
    content_type = ContentType.objects.get_for_model(Order)
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action='UPDATE',
        content_type=content_type,
        object_id=order.id,
        old_values={'workflow_state': old_state_name},
        new_values={'event': 'ORDER_REOPENED_AFTER_ACCIDENTAL_RELEASE', 'workflow_state': target_state.name if target_state else 'Billed'}
    )
    
    messages.success(request, f"Order #{order.id} on Table T{table.number if table else 'N/A'} re-opened successfully!")
    
    if table:
        return redirect('hotel_pos:pos_dashboard_table', table_id=table.id)
    return redirect('hotel_pos:order_history')
