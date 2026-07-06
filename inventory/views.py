from django.shortcuts import render
from django.db.models import Sum, Q, F, FloatField, ExpressionWrapper
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from .models import Item, PurchaseOrder

def dashboard(request):
    total_items = Item.objects.count()
    total_stock = Item.objects.aggregate(Sum('stock_quantity'))['stock_quantity__sum'] or 0
    total_pos = PurchaseOrder.objects.count()
    
    # recent POs
    recent_pos = PurchaseOrder.objects.select_related('vendor', 'workflow_state').order_by('-created_at')[:5]
    
    context = {
        'total_items': total_items,
        'total_stock': total_stock,
        'total_pos': total_pos,
        'recent_pos': recent_pos,
    }
    return render(request, 'inventory/dashboard.html', context)

def po_list(request):
    query = request.GET.get('q', '')
    
    queryset = PurchaseOrder.objects.select_related('vendor', 'workflow_state').order_by('-created_at')
    
    if query:
        queryset = queryset.filter(
            Q(vendor__name__icontains=query) | 
            Q(po_number__icontains=query) |
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
    headers = ['PO Number', 'Vendor', 'Total Amount', 'Status', 'Date']
    context['headers'] = headers
    return TemplateResponse(request, 'inventory/po_list.html', context)

from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from core.models import AuditLog

def po_detail(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.prefetch_related('items__item'), pk=pk)
    
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
    
    queryset = PurchaseOrder.objects.select_related('vendor', 'workflow_state').order_by('-created_at')
    
    if query:
        queryset = queryset.filter(
            Q(vendor__name__icontains=query) | 
            Q(po_number__icontains=query)
        )
        
    fields = [
        ('id', 'System ID'),
        ('po_number', 'PO Number'),
        ('vendor.name', 'Vendor'),
        ('total_amount', 'Total Amount (USD)'),
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
from core.imports.importer import DataImporter
from django.db.models import Count
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_chart(request):
    """HTMX endpoint that returns an interactive Plotly chart of PO Statuses."""
    qs = PurchaseOrder.objects.values('workflow_state__name').annotate(count=Count('id'))
    qs_list = list(qs)
    for i in qs_list:
        if i['workflow_state__name'] is None:
            i['workflow_state__name'] = 'Draft'
            
    html = GraphGenerator.generate_pie_chart(
        queryset=qs_list,
        names_field='workflow_state__name',
        values_field='count',
        title="Purchase Orders by Status"
    )
    return HttpResponse(html)

@login_required
def inventory_valuation_chart(request):
    """HTMX endpoint plotting inventory valuation by category."""
    # Value = stock_quantity * cost_price
    qs = Item.objects.values('category__name').annotate(
        total_value=Sum(
            ExpressionWrapper(F('stock_quantity') * F('cost_price'), output_field=FloatField())
        )
    )
    qs_list = list(qs)
    for i in qs_list:
        if i['category__name'] is None:
            i['category__name'] = 'Uncategorized'
            
    html = GraphGenerator.generate_bar_chart(
        queryset=qs_list,
        x_field='category__name',
        y_field='total_value',
        title="Inventory Valuation by Category",
        labels={'category__name': 'Category', 'total_value': 'Total Value ($)'}
    )
    return HttpResponse(html)

from .services import LedgerService, InsufficientStockError
from .models import Warehouse

@login_required
def item_list(request):
    query = request.GET.get('q', '')
    
    queryset = Item.objects.select_related('category', 'uom').order_by('name')
    
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | 
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )
        
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_url': request.path,
    }
    
    if request.htmx:
        return TemplateResponse(request, 'inventory/partials/item_rows.html', context)
        
    return TemplateResponse(request, 'inventory/item_list.html', context)

@login_required
def barcode_scan(request):
    """HTMX endpoint to quickly receive stock via barcode scan."""
    if request.method == 'POST':
        barcode = request.POST.get('barcode', '').strip()
        if not barcode:
            return TemplateResponse(request, 'inventory/partials/toast.html', {'message': 'No barcode scanned!', 'type': 'error'})
            
        try:
            item = Item.objects.get(barcode=barcode)
            # For MVP, assume we always receive to the first active warehouse
            warehouse = Warehouse.objects.filter(is_active=True).first()
            if not warehouse:
                return TemplateResponse(request, 'inventory/partials/toast.html', {'message': 'No active warehouse configured!', 'type': 'error'})
                
            LedgerService.record_stock_transaction(
                item=item,
                warehouse=warehouse,
                quantity_change=1,
                transaction_type='ADJ',
                reference_document='BARCODE-SCAN',
                user=request.user,
                notes="Quick stock addition via barcode scanner."
            )
            return TemplateResponse(request, 'inventory/partials/toast.html', {'message': f'Successfully added 1 x {item.name}!', 'type': 'success'})
        except Item.DoesNotExist:
            return TemplateResponse(request, 'inventory/partials/toast.html', {'message': f'Barcode {barcode} not found!', 'type': 'error'})
            
    return HttpResponse(status=405)

import uuid
from core.models import State, Workflow
from .models import Vendor, PurchaseOrderItem

@login_required
def po_create(request):
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor')
        warehouse_id = request.POST.get('destination_warehouse')
        
        item_ids = request.POST.getlist('item_id[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('unit_price[]')
        
        vendor = get_object_or_404(Vendor, id=vendor_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        po_number = f"PO-{str(uuid.uuid4())[:8].upper()}"
        
        po = PurchaseOrder.objects.create(
            vendor=vendor,
            destination_warehouse=warehouse,
            po_number=po_number,
            total_amount=0
        )
        
        total = 0
        for i_id, qty, price in zip(item_ids, quantities, prices):
            if i_id and qty and price:
                item = Item.objects.get(id=i_id)
                q = int(qty)
                p = float(price)
                PurchaseOrderItem.objects.create(po=po, item=item, quantity=q, unit_price=p)
                total += (q * p)
                
        po.total_amount = total
        
        try:
            wf = Workflow.objects.get(model_name="inventory.PurchaseOrder")
            draft_state = State.objects.get(workflow=wf, name="Draft")
            po.workflow_state = draft_state
        except (Workflow.DoesNotExist, State.DoesNotExist):
            pass
            
        po.save()
        
        response = HttpResponse()
        response['HX-Redirect'] = f"/inventory/po/{po.id}/"
        return response
        
    context = {
        'vendors': Vendor.objects.all(),
        'warehouses': Warehouse.objects.filter(is_active=True),
        'items': Item.objects.all()
    }
    return TemplateResponse(request, 'inventory/po_create.html', context)

@login_required
def po_add_item_row(request):
    """HTMX endpoint that returns a blank new row for the PO Item Table."""
    context = {'items': Item.objects.all()}
    return TemplateResponse(request, 'inventory/partials/po_item_row.html', context)
