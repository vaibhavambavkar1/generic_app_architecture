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

from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from core.models import AuditLog

def po_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    # Get Audit Logs
    ct = ContentType.objects.get_for_model(PurchaseOrder)
    audit_logs = AuditLog.objects.filter(content_type=ct, object_id=po.id)
    
    context = {
        'po': po,
        'audit_logs': audit_logs,
    }
    return TemplateResponse(request, 'inventory/po_detail.html', context)

from django.http import FileResponse
from .reports import generate_po_pdf

def po_pdf_export(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    pdf_buffer = generate_po_pdf(po)
    
    return FileResponse(
        pdf_buffer, 
        as_attachment=True, 
        filename=f"PO_{po.id:04d}.pdf"
    )

from django.http import HttpResponse
from core.reports.exporter import DataExporter

def po_bulk_export(request, fmt):
    query = request.GET.get('q', '')
    
    queryset = PurchaseOrder.objects.select_related('item', 'workflow_state').order_by('-created_at')
    
    if query:
        queryset = queryset.filter(
            Q(item__name__icontains=query) | 
            Q(id__icontains=query)
        )
        
    fields = [
        ('id', 'PO Number'),
        ('item.name', 'Item Name'),
        ('item.sku', 'SKU'),
        ('quantity', 'Quantity'),
        ('total_cost', 'Total Cost (USD)'),
        ('workflow_state.name', 'Status'),
        ('created_at', 'Date Created')
    ]
    
    if fmt == 'csv':
        buffer = DataExporter.export_csv(queryset, fields)
        return FileResponse(buffer, as_attachment=True, filename='purchase_orders.csv')
    elif fmt == 'excel':
        buffer = DataExporter.export_excel(queryset, fields)
        return FileResponse(buffer, as_attachment=True, filename='purchase_orders.xlsx')
    elif fmt == 'json':
        buffer = DataExporter.export_json(queryset, fields)
        return FileResponse(buffer, as_attachment=True, filename='purchase_orders.json')
    
    return HttpResponse("Unsupported format", status=400)
