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

def item_import(request):
    if request.method == 'POST':
        if 'import_file' not in request.FILES:
            return HttpResponse("No file uploaded", status=400)
            
        file = request.FILES['import_file']
        
        # Determine format from extension
        ext = file.name.split('.')[-1].lower()
        if ext == 'csv':
            fmt = 'csv'
        elif ext in ['xlsx', 'xls']:
            fmt = 'excel'
        elif ext == 'json':
            fmt = 'json'
        else:
            return HttpResponse("Unsupported file type", status=400)
            
        mapping = {
            'SKU': 'sku',
            'Name': 'name',
            'Stock Quantity': 'stock_quantity'
        }
        
        results = DataImporter.import_data(
            app_label='inventory',
            model_name='item',
            file_stream=file,
            fmt=fmt,
            mapping=mapping,
            unique_fields=['sku']
        )
        
        context = {'results': results}
        return TemplateResponse(request, 'inventory/modals/import_results.html', context)
        
    return TemplateResponse(request, 'inventory/modals/import_items.html')

from core.reports.graphs import GraphGenerator
from django.db.models import Count

@login_required
def dashboard_chart(request):
    """HTMX endpoint that returns an interactive Plotly chart of PO Statuses."""
    # Group POs by status
    qs = PurchaseOrder.objects.values('workflow_state__name').annotate(count=Count('id'))
    
    # We must convert it to a list to handle Null names if we want, but plotly handles None.
    qs_list = list(qs)
    for item in qs_list:
        if item['workflow_state__name'] is None:
            item['workflow_state__name'] = 'Draft'
            
    # Mocking queryset behavior for GraphGenerator which expects .values() but we give a list of dicts.
    # Wait, GraphGenerator does `list(queryset.values())`, so it expects a queryset.
    # We should just let GraphGenerator handle a list of dicts directly!
    
    # Actually, we should tweak GraphGenerator to support lists of dicts directly in case we pass pre-aggregated data.
    # I'll pass the list directly and map 'workflow_state__name' to 'count'.
    html = GraphGenerator.generate_pie_chart(
        queryset=qs_list,
        names_field='workflow_state__name',
        values_field='count',
        title="Purchase Orders by Status"
    )
    
    return HttpResponse(html)
