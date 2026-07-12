import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.urls import reverse

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .models import Supplier, InventoryItem, PurchaseOrder, POLineItem, SupplierCatalogItem
from .forms import InventoryItemForm, SupplierForm, PurchaseOrderForm, SupplierCatalogProductForm
from core.models import AuditLog, State, Transition
from core.reports.graphs import GraphGenerator

@login_required
def dashboard(request):
    """
    Overview page with key KPIs and interactive charts.
    """
    total_items = InventoryItem.objects.count()
    low_stock_items = InventoryItem.objects.filter(stock_level__lte=F('reorder_threshold')).count()
    total_suppliers = Supplier.objects.count()
    
    # Calculate stock value: Sum of (stock_level * unit_price)
    stock_value = InventoryItem.objects.aggregate(
        total=Sum(ExpressionWrapper(F('stock_level') * F('unit_price'), output_field=DecimalField()))
    )['total'] or 0.00
    
    # Generate Chart 1: Stock levels bar chart
    items_qs = InventoryItem.objects.all()[:15]
    stock_chart = GraphGenerator.generate_bar_chart(
        queryset=items_qs,
        x_field='name',
        y_field='stock_level',
        title="Stock Levels by Product"
    )
    
    # Generate Chart 2: Purchase Order status distribution
    po_states_data = list(
        PurchaseOrder.objects.values('workflow_state__name')
        .annotate(total=Sum('total_amount'))
    )
    # Rename key for the pie chart generator
    for item in po_states_data:
        item['status_name'] = item['workflow_state__name'] or 'Draft'
        
    po_chart = GraphGenerator.generate_pie_chart(
        queryset=po_states_data,
        names_field='status_name',
        values_field='total',
        title="Purchase Orders by Status"
    )

    # Generate Chart 3: Demand Forecast Chart based on received PO line item history
    from django.db.models.functions import TruncDate
    historical_orders = list(
        POLineItem.objects.filter(purchase_order__workflow_state__name='Received')
        .annotate(order_date=TruncDate('purchase_order__created_at'))
        .values('order_date')
        .annotate(quantity_ordered=Sum('quantity'))
        .order_by('order_date')
    )
    
    # Format dates and quantities for Plotly
    plotly_data = []
    for order in historical_orders:
        plotly_data.append({
            'date': str(order['order_date']),
            'total_qty': float(order['quantity_ordered'])
        })
        
    forecast_chart = GraphGenerator.generate_forecast_chart(
        historical_data=plotly_data,
        x_field='date',
        y_field='total_qty',
        title="Procurement Demand Trend & Forecast"
    )

    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'total_suppliers': total_suppliers,
        'stock_value': stock_value,
        'stock_chart': stock_chart,
        'po_chart': po_chart,
        'forecast_chart': forecast_chart
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def item_list(request):
    """List of all inventory items with filter options."""
    query = request.GET.get('q', '')
    low_stock = request.GET.get('low_stock', '')

    items = InventoryItem.objects.all()
    if query:
        items = items.filter(name__icontains=query) | items.filter(sku__icontains=query)
    if low_stock == '1':
        items = items.filter(stock_level__lte=F('reorder_threshold'))

    context = {
        'items': items,
        'query': query,
        'low_stock': low_stock
    }
    return render(request, 'inventory/item_list.html', context)

@login_required
def supplier_list(request):
    """List of all suppliers."""
    suppliers = Supplier.objects.all().prefetch_related('supplied_items')
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def po_list(request):
    """List of all purchase orders."""
    pos = PurchaseOrder.objects.all().select_related('supplier', 'workflow_state').order_by('-created_at')
    return render(request, 'inventory/po_list.html', {'purchase_orders': pos})

@login_required
def po_detail(request, pk):
    """Detailed view of a Purchase Order, including its lines, workflow actions, and audit logs."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    # Fetch audit logs
    content_type = ContentType.objects.get_for_model(po)
    audit_logs = AuditLog.objects.filter(
        content_type=content_type,
        object_id=po.id
    ).select_related('user').order_by('-timestamp')

    context = {
        'instance': po,
        'lines': po.lines.all().select_related('item'),
        'transitions': po.get_available_transitions(request.user),
        'app_label': 'inventory',
        'model_name': 'purchaseorder',
        'audit_logs': audit_logs
    }
    return render(request, 'inventory/po_detail.html', context)

@login_required
@transaction.atomic
def po_create(request):
    """Create a new Purchase Order along with its lines."""
    suppliers = Supplier.objects.all()
    items = InventoryItem.objects.all().prefetch_related('catalog_items')

    if request.method == 'POST':
        po_number = request.POST.get('po_number')
        supplier_id = request.POST.get('supplier')
        
        supplier = get_object_or_404(Supplier, id=supplier_id)
        
        # Create PurchaseOrder (starts in the Initial state 'Draft')
        draft_state = State.objects.filter(workflow__model_name='inventory.PurchaseOrder', is_initial=True).first()
        
        po_kwargs = {
            'supplier': supplier,
            'workflow_state': draft_state,
        }
        if po_number:
            po_kwargs['po_number'] = po_number
            
        po = PurchaseOrder.objects.create(**po_kwargs)
        
        # Read form items
        item_ids = request.POST.getlist('item[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        
        total = 0.00
        for item_id, qty, price in zip(item_ids, quantities, prices):
            if not item_id or not qty or not price:
                continue
            item = get_object_or_404(InventoryItem, id=item_id)
            q = int(qty)
            p = float(price)
            POLineItem.objects.create(
                purchase_order=po,
                item=item,
                quantity=q,
                unit_price=p
            )
            total += (q * p)
            
        po.total_amount = total
        po.save()
        
        return redirect(reverse('inventory:po_detail', args=[po.id]))

    context = {
        'suppliers': suppliers,
        'items': items
    }
    return render(request, 'inventory/po_create.html', context)

def generate_po_pdf_bytes(po):
    """Generates a professional PDF receipt for a Purchase Order and returns bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e3a8a'), # Premium Navy
        spaceAfter=15
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#334155'), # Slate Gray
        spaceBefore=10,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )
    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    # 1. Document Title
    story.append(Paragraph("PURCHASE ORDER", title_style))
    story.append(Spacer(1, 10))

    # 2. Metadata details (2-column layout)
    meta_data = [
        [
            Paragraph(f"<b>PO Number:</b> {po.po_number}", body_style),
            Paragraph(f"<b>Supplier:</b> {po.supplier.name}", body_style)
        ],
        [
            Paragraph(f"<b>Date Created:</b> {po.created_at.strftime('%Y-%m-%d %H:%M')}", body_style),
            Paragraph(f"<b>Contact Email:</b> {po.supplier.contact_email}", body_style)
        ],
        [
            Paragraph(f"<b>Status:</b> {po.workflow_state.name if po.workflow_state else 'Draft'}", body_style),
            Paragraph(f"<b>Phone:</b> {po.supplier.phone or 'N/A'}", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # 3. Line Items Table
    story.append(Paragraph("Line Items", section_heading))
    
    # Table headers
    headers = [
        Paragraph("SKU", header_style),
        Paragraph("Product Name", header_style),
        Paragraph("Quantity", header_style),
        Paragraph("Unit Price", header_style),
        Paragraph("Subtotal", header_style)
    ]
    table_data = [headers]
    
    # Table rows
    for line in po.lines.all().select_related('item'):
        table_data.append([
            Paragraph(line.item.sku, body_style),
            Paragraph(line.item.name, body_style),
            Paragraph(str(line.quantity), body_style),
            Paragraph(f"${line.unit_price:.2f}", body_style),
            Paragraph(f"${line.subtotal:.2f}", body_bold)
        ])
        
    # Total row
    table_data.append([
        Paragraph("<b>Total Amount:</b>", body_bold),
        "", "", "",
        Paragraph(f"<b>${po.total_amount:.2f}</b>", body_bold)
    ])
    
    items_table = Table(table_data, colWidths=[100, 200, 70, 80, 90])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#e2e8f0')),
        ('SPAN', (0,-1), (3,-1)), # Span "Total Amount" label across first 4 columns
        ('ALIGN', (0,-1), (3,-1), 'RIGHT'),
        ('TOPPADDING', (0,-1), (-1,-1), 10),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor('#94a3b8')),
    ]))
    story.append(items_table)
    
    # Build Document
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


@login_required
def po_download_pdf(request, pk):
    """Generates and downloads a professional PDF receipt for a Purchase Order."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    pdf_bytes = generate_po_pdf_bytes(po)
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PO_{po.po_number}.pdf"'
    return response

# --- InventoryItem CRUD ---
@login_required
def item_create(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:item_list')
    else:
        form = InventoryItemForm()
    return render(request, 'inventory/form.html', {'form': form, 'title': 'Create Product', 'back_url': reverse('inventory:item_list')})

@login_required
def item_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('inventory:item_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'inventory/form.html', {'form': form, 'title': f'Edit Product: {item.sku}', 'back_url': reverse('inventory:item_list')})

@login_required
def item_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('inventory:item_list')
    return render(request, 'inventory/delete_confirm.html', {'object': item, 'title': f'Delete Product: {item.sku}', 'back_url': reverse('inventory:item_list')})


# --- Supplier CRUD ---
@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'inventory/form.html', {'form': form, 'title': 'Create Supplier', 'back_url': reverse('inventory:supplier_list')})

@login_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'inventory/form.html', {'form': form, 'title': f'Edit Supplier: {supplier.name}', 'back_url': reverse('inventory:supplier_list')})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/delete_confirm.html', {'object': supplier, 'title': f'Delete Supplier: {supplier.name}', 'back_url': reverse('inventory:supplier_list')})

@login_required
def supplier_catalog_modal(request, pk, form=None):
    """Render the catalog management modal for a supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    items = InventoryItem.objects.all().order_by('name')
    catalog_items = supplier.catalog_entries.all().select_related('item')
    if form is None:
        form = SupplierCatalogProductForm()
    context = {
        'supplier': supplier,
        'items': items,
        'catalog_items': catalog_items,
        'form': form,
    }
    return render(request, 'inventory/supplier_catalog_modal.html', context)

@login_required
@transaction.atomic
def supplier_catalog_add_product(request, pk):
    """Create a new product and add it to the supplier's catalog."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierCatalogProductForm(request.POST)
        if form.is_valid():
            item = form.save()
            SupplierCatalogItem.objects.create(
                supplier=supplier,
                item=item,
                price=form.cleaned_data['supplier_price']
            )
            return supplier_catalog_modal(request, pk)
    else:
        form = SupplierCatalogProductForm()
    return supplier_catalog_modal(request, pk, form=form)

@login_required
@transaction.atomic
def supplier_catalog_remove(request, entry_pk):
    """Remove an item from the supplier's catalog."""
    entry = get_object_or_404(SupplierCatalogItem, pk=entry_pk)
    supplier_id = entry.supplier_id
    entry.delete()
    return supplier_catalog_modal(request, supplier_id)


# --- PurchaseOrder Delete ---
@login_required
def po_delete(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if po.workflow_state and po.workflow_state.name != 'Draft':
        return HttpResponse("Deletion only allowed for Draft Purchase Orders.", status=403)
        
    if request.method == 'POST':
        po.delete()
        return redirect('inventory:po_list')
    return render(request, 'inventory/delete_confirm.html', {'object': po, 'title': f'Delete Purchase Order: {po.po_number}', 'back_url': reverse('inventory:po_detail', args=[po.id])})


@login_required
def item_price_history(request, pk):
    """
    Renders price history for a specific inventory product.
    If requested via HTMX, returns an overlay modal fragment.
    """
    item = get_object_or_404(InventoryItem, pk=pk)
    logs = list(item.price_logs.all().order_by('changed_at'))
    
    price_logs_with_diff = []
    prev_price = None
    
    for log in logs:
        diff_pct = 0.0
        if prev_price is not None and prev_price != 0:
            diff_pct = float((log.price - prev_price) / prev_price) * 100
        
        log.diff_pct = diff_pct
        prev_price = log.price
        price_logs_with_diff.append(log)
        
    price_logs_with_diff.reverse()
    
    context = {
        'item': item,
        'price_logs': price_logs_with_diff,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'inventory/item_price_history_modal.html', context)
        
    return render(request, 'inventory/item_price_history.html', context)


@login_required
@transaction.atomic
def po_edit(request, pk):
    """Edit a Purchase Order in Draft state."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    # Security/state check: Only Draft POs can be edited
    if po.workflow_state and po.workflow_state.name != 'Draft':
        return HttpResponse("Editing is only allowed for Draft Purchase Orders.", status=403)
        
    suppliers = Supplier.objects.all()
    items = InventoryItem.objects.all().prefetch_related('catalog_items')
    
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        supplier = get_object_or_404(Supplier, id=supplier_id)
        
        po.supplier = supplier
        
        # Clear existing line items and rebuild
        po.lines.all().delete()
        
        # Read form items
        item_ids = request.POST.getlist('item[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        
        total = 0.00
        for item_id, qty, price in zip(item_ids, quantities, prices):
            if not item_id or not qty or not price:
                continue
            item = get_object_or_404(InventoryItem, id=item_id)
            q = int(qty)
            p = float(price)
            POLineItem.objects.create(
                purchase_order=po,
                item=item,
                quantity=q,
                unit_price=p
            )
            total += (q * p)
            
        po.total_amount = total
        po.save()
        
        return redirect(reverse('inventory:po_detail', args=[po.id]))
        
    # Serialize existing line items to JSON for Alpine.js initialization
    import json
    lines_data = []
    for line in po.lines.all():
        lines_data.append({
            'item_id': str(line.item.id),
            'quantity': line.quantity,
            'price': float(line.unit_price)
        })
        
    context = {
        'po': po,
        'suppliers': suppliers,
        'items': items,
        'lines_json': json.dumps(lines_data),
    }
    return render(request, 'inventory/po_edit.html', context)


@login_required
def po_receive_modal(request, pk, transition_id):
    """Render the modal content for validating the received stock."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    transition = get_object_or_404(Transition, id=transition_id)
    return render(request, 'inventory/po_receive_modal.html', {
        'po': po,
        'transition': transition
    })


@login_required
@transaction.atomic
def po_receive_submit(request, pk, transition_id):
    """Process the submitted received stock validation and transition the PO state."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    transition = get_object_or_404(Transition, id=transition_id)
    
    # Update lines with actual received values and expiry dates
    line_ids = request.POST.getlist('line_id[]')
    
    for line_id in line_ids:
        line = get_object_or_404(POLineItem, id=line_id, purchase_order=po)
        
        qty_str = request.POST.get(f'received_qty_{line_id}')
        price_str = request.POST.get(f'received_price_{line_id}')
        expiry_date = request.POST.get(f'expiry_date_{line_id}')
        
        if qty_str is not None:
            line.received_quantity = int(qty_str)
        if price_str is not None:
            line.received_unit_price = float(price_str)
        if expiry_date:
            line.expiry_date = expiry_date
        line.save()
        
    # Execute workflow transition
    try:
        po.transition_to(transition, request.user)
    except ValueError as e:
        return HttpResponse(f"Transition error: {str(e)}", status=400)
        
    # Return HX-Refresh header to reload the full PO detail page with updated stock levels/totals
    response = HttpResponse()
    response['HX-Refresh'] = 'true'
    return response


from django.core.mail import EmailMessage

@login_required
def po_email_modal(request, pk):
    """Render the modal content for sending PO via email."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if not po.workflow_state or po.workflow_state.name != "Approved":
        return HttpResponse("Email can only be sent for Approved Purchase Orders.", status=403)
        
    default_subject = f"Purchase Order {po.po_number} - ERP Framework"
    
    body_lines = [
        f"Dear {po.supplier.name},",
        "",
        f"Please find attached our Purchase Order {po.po_number} containing the following requested items:",
        ""
    ]
    for line in po.lines.all().select_related('item'):
        body_lines.append(f"- {line.item.name} (SKU: {line.item.sku}): {line.quantity} units @ ${line.unit_price:.2f}/unit")
    body_lines.extend([
        "",
        f"Total Estimated Value: ${po.total_amount:.2f}",
        "",
        "Please review the attached PDF document for our full terms and shipping/billing information.",
        "Confirm receipt and estimated delivery date by replying to this email.",
        "",
        "Best regards,",
        "Procurement Team",
        "ERP Framework"
    ])
    default_body = "\n".join(body_lines)
    
    return render(request, 'inventory/po_email_modal.html', {
        'po': po,
        'default_subject': default_subject,
        'default_body': default_body
    })


@login_required
def po_email_submit(request, pk):
    """Process the submitted PO email and open the local email client pre-filled with details."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if not po.workflow_state or po.workflow_state.name != "Approved":
        return HttpResponse("Email can only be sent for Approved Purchase Orders.", status=403)
        
    recipient = request.POST.get('email')
    subject = request.POST.get('subject')
    body = request.POST.get('body')
    
    if not recipient or not subject or not body:
        return HttpResponse("All fields (Recipient, Subject, Body) are required.", status=400)
        
    from django.utils.html import escapejs
    
    # Return HTMX response with OOB toast and client-side JS redirection to mailto:
    response_content = (
        f'<div hx-swap-oob="beforeend:body">'
        f'  <div class="toast toast-end z-50">'
        f'    <div class="alert alert-success shadow-lg rounded-xl flex gap-2 font-semibold text-white">'
        f'      <span>Opening email client...</span>'
        f'    </div>'
        f'  </div>'
        f'</div>'
        f'<script>'
        f'  document.getElementById("po_email_modal")?.remove();'
        f'  const recipient = "{escapejs(recipient)}";'
        f'  const subject = "{escapejs(subject)}";'
        f'  const body = "{escapejs(body)}";'
        f'  window.location.href = "mailto:" + recipient + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);'
        f'</script>'
    )
    return HttpResponse(response_content)




