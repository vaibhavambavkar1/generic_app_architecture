from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db import transaction
from django.contrib import messages
from .models import Quotation, SalesOrder, POSInvoice, POSLineItem
from generic_store_mgmt.models import Product
from inventory.models import Warehouse
from django.urls import reverse
import uuid

@login_required
def quotation_list(request):
    quotes = Quotation.objects.all().order_by('-created_at')
    return render(request, 'sales/quotation_list.html', {'quotes': quotes})

from .forms import QuotationLineItemForm, QuotationForm, SalesOrderForm
from .models import QuotationLineItem

@login_required
def quotation_create_modal(request):
    if request.method == "POST":
        form = QuotationForm(request.POST)
        if form.is_valid():
            quote = form.save()
            messages.success(request, f"Quotation #{quote.quote_number} created.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('sales:quotation_detail', args=[quote.pk])
                return response
            return redirect('sales:quotation_detail', pk=quote.pk)
    else:
        form = QuotationForm()
    return render(request, 'sales/quotation_create_modal.html', {'form': form})

@login_required
def sales_order_create_modal(request):
    if request.method == "POST":
        form = SalesOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f"Sales Order #{order.so_number} created.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('sales:sales_order_detail', args=[order.pk])
                return response
            return redirect('sales:sales_order_detail', pk=order.pk)
    else:
        form = SalesOrderForm()
    return render(request, 'sales/sales_order_create_modal.html', {'form': form})

@login_required
def quotation_detail(request, pk):
    quote = get_object_or_404(Quotation, pk=pk)
    
    if request.method == "POST" and request.POST.get('action') == 'send':
        try:
            quote.send_quote()
            quote.save()
            messages.success(request, f"Quotation #{quote.quote_number} sent to {quote.customer.name}.")
        except Exception as e:
            messages.error(request, f"Failed to send: {str(e)}")
            
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
        return redirect('sales:quotation_detail', pk=pk)
        
    item_form = QuotationLineItemForm()
    return render(request, 'sales/quotation_detail.html', {'quote': quote, 'item_form': item_form})

@login_required
def quotation_add_item(request, pk):
    quote = get_object_or_404(Quotation, pk=pk)
    if request.method == "POST":
        form = QuotationLineItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.quotation = quote
            item.save()
            
            # Update total
            quote.total_amount = sum(i.quantity * i.unit_price for i in quote.lines.all())
            quote.save()
            messages.success(request, "Item added to quotation.")
        else:
            messages.error(request, "Failed to add item.")
            
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('sales:quotation_detail', pk=pk)

@login_required
def quotation_delete_item(request, item_pk):
    item = get_object_or_404(QuotationLineItem, pk=item_pk)
    quote = item.quotation
    item.delete()
    
    # Update total
    quote.total_amount = sum(i.quantity * i.unit_price for i in quote.lines.all())
    quote.save()
    
    messages.success(request, "Item removed.")
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('sales:quotation_detail', pk=quote.pk)

@login_required
def quotation_send_modal(request, pk):
    quote = get_object_or_404(Quotation, pk=pk)
    return render(request, 'sales/quotation_send_modal.html', {'quote': quote})

@login_required
def sales_order_list(request):
    orders = SalesOrder.objects.all().order_by('-created_at')
    return render(request, 'sales/sales_order_list.html', {'orders': orders})

@login_required
def sales_order_detail(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    return render(request, 'sales/sales_order_detail.html', {'order': order})

# --- POS Terminal ---

@login_required
def pos_terminal(request):
    # Retrieve active draft invoice from session, or create one
    invoice_id = request.session.get('active_pos_invoice_id')
    invoice = None
    if invoice_id:
        invoice = POSInvoice.objects.filter(id=invoice_id, is_paid=False).first()
    
    if not invoice:
        # Get a default warehouse, typically mapped to user, but fallback to first
        warehouse = Warehouse.objects.first()
        if not warehouse:
            return HttpResponse("Please create a Warehouse first.", status=400)
            
        invoice = POSInvoice.objects.create(
            invoice_number=f"INV-{str(uuid.uuid4())[:8].upper()}",
            warehouse=warehouse
        )
        request.session['active_pos_invoice_id'] = invoice.id

    return render(request, 'sales/pos_terminal.html', {'invoice': invoice})

@login_required
def pos_scan_barcode(request):
    barcode = request.POST.get('barcode', '').strip()
    invoice_id = request.session.get('active_pos_invoice_id')
    invoice = get_object_or_404(POSInvoice, id=invoice_id, is_paid=False)

    if barcode:
        # Check by SKU or barcode (assuming SKU matches barcode for simple POS)
        product = Product.objects.filter(sku=barcode).first()
        if product:
            # Check price list
            price = 0.00
            # For simplicity, if we have price_list_items, take the first active one, or standard fallback
            pli = product.price_list_items.first()
            if pli:
                price = pli.price
            
            # Add to cart
            line, created = POSLineItem.objects.get_or_create(
                invoice=invoice,
                product=product,
                defaults={'quantity': 1, 'unit_price': price, 'line_total': price}
            )
            if not created:
                line.quantity += 1
                line.line_total = line.quantity * line.unit_price
                line.save()
                
            # Update invoice total
            invoice.subtotal = sum(item.line_total for item in invoice.lines.all())
            invoice.total_amount = invoice.subtotal + invoice.tax_amount
            invoice.save()
        else:
            # Product not found, send HTMX error Toast or inline message
            return HttpResponse(
                f"<div class='alert alert-error' hx-swap-oob='true' id='pos-alert'>Product with SKU {barcode} not found!</div>"
            )

    # Return updated cart fragment
    return render(request, 'sales/partials/pos_cart.html', {'invoice': invoice})

@login_required
def pos_remove_item(request, item_id):
    invoice_id = request.session.get('active_pos_invoice_id')
    invoice = get_object_or_404(POSInvoice, id=invoice_id, is_paid=False)
    line = get_object_or_404(POSLineItem, id=item_id, invoice=invoice)
    line.delete()
    
    # Update total
    invoice.subtotal = sum(item.line_total for item in invoice.lines.all())
    invoice.total_amount = invoice.subtotal + invoice.tax_amount
    invoice.save()

    return render(request, 'sales/partials/pos_cart.html', {'invoice': invoice})

@login_required
def pos_checkout(request):
    invoice_id = request.session.get('active_pos_invoice_id')
    invoice = get_object_or_404(POSInvoice, id=invoice_id, is_paid=False)
    
    if request.method == "POST":
        payment_method = request.POST.get('payment_method', 'CASH')
        invoice.payment_method = payment_method
        
        with transaction.atomic():
            invoice.process_payment() # Sets is_paid and writes Ledger
            
        # Clear session
        del request.session['active_pos_invoice_id']
        
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = reverse('sales:pos_receipt', args=[invoice.id])
            return response
        return redirect('sales:pos_receipt', pk=invoice.id)
        
    return render(request, 'sales/pos_checkout_modal.html', {'invoice': invoice})

@login_required
def pos_receipt(request, pk):
    invoice = get_object_or_404(POSInvoice, pk=pk)
    return render(request, 'sales/pos_receipt.html', {'invoice': invoice})
