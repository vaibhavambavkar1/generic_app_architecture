from django.shortcuts import render
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
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

def po_list(request):
    query = request.GET.get('q', '')
    
    queryset = PurchaseOrder.objects.select_related('item', 'workflow_state').order_by('-created_at')
    
    if query:
        queryset = queryset.filter(
            Q(item__name__icontains=query) | 
            Q(id__icontains=query)
        )
        
    paginator = Paginator(queryset, 10) # 10 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'search_url': request.path,
    }
    
    # If HTMX request, just return the rows snippet
    if request.htmx:
        return TemplateResponse(request, 'inventory/partials/po_rows.html', context)
        
    # Otherwise return the full page
    headers = ['ID', 'Item', 'Qty', 'Total Cost', 'Status', 'Date']
    context['headers'] = headers
    return TemplateResponse(request, 'inventory/po_list.html', context)
