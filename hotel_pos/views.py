from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Order, OrderItem, MenuItem, Table
import json

def pos_dashboard(request):
    """ HTMX powered POS dashboard """
    categories = [] # Would fetch from MenuCategory
    items = MenuItem.objects.filter(is_active=True)
    tables = Table.objects.filter(is_active=True)
    context = {
        'items': items,
        'tables': tables
    }
    return render(request, 'hotel_pos/pos_dashboard.html', context)

def add_to_order(request, item_id):
    """ HTMX endpoint to add item to current order """
    item = get_object_or_404(MenuItem, id=item_id)
    # Basic stub for adding item
    return HttpResponse(f"<li class='p-2 border-b'>{item.name} - ${item.price}</li>")

def kitchen_display_system(request):
    """ Kitchen Display System (KDS) """
    # Fetch OrderItems that are in 'Cooking' state
    # Stubbing for now as workflow states require DB setup
    active_kots = OrderItem.objects.all()[:10] 
    return render(request, 'hotel_pos/kds.html', {'kots': active_kots})

def receipt_printer(request, order_id):
    """ View for Thermal Receipt Printer """
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    return render(request, 'hotel_pos/receipt_printer.html', {'order': order, 'items': items})
