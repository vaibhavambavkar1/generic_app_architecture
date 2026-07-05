from django.shortcuts import render
from django.db.models import Sum
from .models import Item, PurchaseOrder

def dashboard(request):
    total_items = Item.objects.count()
    total_stock = Item.objects.aggregate(Sum('stock_quantity'))['stock_quantity__sum'] or 0
    total_pos = PurchaseOrder.objects.count()
    
    # recent POs
    recent_pos = PurchaseOrder.objects.select_related('item', 'workflow_state').order_by('-created_at')[:5]
    
    context = {
        'total_items': total_items,
        'total_stock': total_stock,
        'total_pos': total_pos,
        'recent_pos': recent_pos,
    }
    return render(request, 'inventory/dashboard.html', context)
