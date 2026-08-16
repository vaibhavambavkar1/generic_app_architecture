from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Account, JournalEntry, JournalEntryLine
from .forms import JournalEntryForm, JournalEntryLineForm, AccountForm
from django.core.paginator import Paginator

@login_required
def account_list(request):
    accounts_list = Account.objects.all().order_by('category', 'code')
    paginator = Paginator(accounts_list, 10)
    page_number = request.GET.get('page')
    accounts = paginator.get_page(page_number)
    return render(request, 'finance/account_list.html', {'accounts': accounts})

@login_required
def account_create(request):
    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            acc = form.save()
            messages.success(request, f"Account {acc.code} created successfully.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('finance:account_list')
    else:
        form = AccountForm()
    return render(request, 'finance/account_create_modal.html', {'form': form})

@login_required
def journal_list(request):
    entries_list = JournalEntry.objects.all().order_by('-date', '-id')
    paginator = Paginator(entries_list, 10)
    page_number = request.GET.get('page')
    entries = paginator.get_page(page_number)
    return render(request, 'finance/journal_list.html', {'entries': entries})

@login_required
def journal_create(request):
    if request.method == "POST":
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            je = form.save()
            return redirect('finance:journal_detail', pk=je.pk)
    else:
        form = JournalEntryForm()
    return render(request, 'finance/journal_form.html', {'form': form})

@login_required
def journal_detail(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == "POST":
        if je.is_posted:
            messages.error(request, "Cannot modify a posted journal entry.")
        else:
            line_form = JournalEntryLineForm(request.POST)
            if line_form.is_valid():
                line = line_form.save(commit=False)
                line.journal_entry = je
                
                if line.debit > 0 and line.credit > 0:
                    messages.error(request, "A line cannot have both Debit and Credit.")
                elif line.debit == 0 and line.credit == 0:
                    messages.error(request, "A line must have either Debit or Credit.")
                else:
                    line.save()
                    messages.success(request, "Line added.")
            else:
                messages.error(request, "Invalid form.")
                
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
        return redirect('finance:journal_detail', pk=pk)
        
    line_form = JournalEntryLineForm()
    total_debit = sum(l.debit for l in je.lines.all())
    total_credit = sum(l.credit for l in je.lines.all())
    
    context = {
        'je': je,
        'line_form': line_form,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit and total_debit > 0
    }
    return render(request, 'finance/journal_detail.html', context)

@login_required
def journal_post(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    if not je.is_posted:
        total_debit = sum(l.debit for l in je.lines.all())
        total_credit = sum(l.credit for l in je.lines.all())
        if total_debit == total_credit and total_debit > 0:
            je.is_posted = True
            je.save()
            messages.success(request, "Journal Entry posted successfully.")
        else:
            messages.error(request, "Cannot post: Debits and Credits must balance and be > 0.")
            
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('finance:journal_detail', pk=pk)

@login_required
def account_edit(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    if request.method == "POST":
        form = AccountForm(request.POST, instance=acc)
        if form.is_valid():
            form.save()
            messages.success(request, f"Account {acc.code} updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('finance:account_list')
    else:
        form = AccountForm(instance=acc)
    return render(request, 'finance/account_edit_modal.html', {'form': form, 'account': acc})

@login_required
def account_delete(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    if request.method == "POST":
        if acc.journal_lines.exists():
            messages.error(request, f"Cannot delete Account {acc.code} because it has associated Journal Entries.")
        else:
            acc.delete()
            messages.success(request, f"Account {acc.code} deleted.")
        return redirect('finance:account_list')
    return redirect('finance:account_list')

@login_required
def journal_edit(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    if je.is_posted:
        messages.error(request, "Cannot edit a posted journal entry.")
        return redirect('finance:journal_list')
        
    if request.method == "POST":
        form = JournalEntryForm(request.POST, instance=je)
        if form.is_valid():
            form.save()
            messages.success(request, f"Journal Entry {je.entry_number} updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('finance:journal_list')
    else:
        form = JournalEntryForm(instance=je)
    return render(request, 'finance/journal_edit_modal.html', {'form': form, 'je': je})

@login_required
def journal_delete(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    if request.method == "POST":
        if je.is_posted:
            messages.error(request, "Cannot delete a posted journal entry.")
        else:
            je.delete()
            messages.success(request, f"Journal Entry {je.entry_number} deleted.")
        return redirect('finance:journal_list')
    return redirect('finance:journal_list')

# --- AR/AP Invoicing Dashboard ---

from core.models import PaymentTransaction, PaymentMethod



@login_required
def process_invoice_payment(request, invoice_type, pk):
    """
    HTMX Modal endpoint to allocate a payment to an AR/AP invoice.
    """
    if invoice_type == 'ar':
        invoice = get_object_or_404(B2BSalesInvoice, pk=pk)
        title = f"Receive Payment for {invoice.invoice_number}"
        balance_due = invoice.total_amount - invoice.amount_paid
        action_url = f"/finance/invoicing/pay/ar/{pk}/"
    else:
        invoice = get_object_or_404(SupplierBill, pk=pk)
        title = f"Send Payment for {invoice.bill_number}"
        balance_due = invoice.total_amount - invoice.amount_paid
        action_url = f"/finance/invoicing/pay/ap/{pk}/"
        
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    if request.method == "POST":
        amount = float(request.POST.get('amount', 0))
        method_id = request.POST.get('payment_method')
        reference = request.POST.get('reference', '')
        
        if amount <= 0 or amount > balance_due:
            messages.error(request, "Invalid payment amount.")
        else:
            method = get_object_or_404(PaymentMethod, pk=method_id)
            
            # Create Generic Payment
            pt = PaymentTransaction.objects.create(
                payment_method=method,
                amount=amount,
                transaction_type='IN' if invoice_type == 'ar' else 'OUT',
                status='SUCCESS',
                notes=reference
            )
            
            # Create Allocation (triggers Journal Entry in save)
            if invoice_type == 'ar':
                InvoicePaymentAllocation.objects.create(payment=pt, sales_invoice=invoice, allocated_amount=amount)
            else:
                InvoicePaymentAllocation.objects.create(payment=pt, supplier_bill=invoice, allocated_amount=amount)
                
            messages.success(request, f"Payment of {amount} processed successfully.")
            
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
        
    context = {
        'title': title,
        'balance_due': balance_due,
        'action_url': action_url,
        'payment_methods': payment_methods
    }
    return render(request, 'finance/invoicing/payment_modal.html', context)

import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

@login_required
def generate_b2b_invoice_pdf(request, pk):
    """
    Generates a professional PDF invoice using ReportLab.
    """
    invoice = get_object_or_404(B2BSalesInvoice, pk=pk)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=20
    )
    
    elements.append(Paragraph("TAX INVOICE", title_style))
    
    # Header Information
    header_data = [
        ["Invoice Number:", invoice.invoice_number, "Date:", invoice.issue_date.strftime("%b %d, %Y")],
        ["Customer:", invoice.customer.get_full_name() or invoice.customer.username, "Due Date:", invoice.due_date.strftime("%b %d, %Y")],
        ["Status:", invoice.status, "Balance Due:", f"Rs {invoice.total_amount - invoice.amount_paid}"]
    ]
    
    t_header = Table(header_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 2*inch])
    t_header.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#333333")),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    
    elements.append(t_header)
    elements.append(Spacer(1, 30))
    
    # Line Items Table
    line_data = [["Product Description", "Qty", "Unit Price", "Total"]]
    
    for line in invoice.lines.all():
        line_data.append([
            line.product.name,
            str(line.quantity),
            f"Rs {line.unit_price}",
            f"Rs {line.line_total}"
        ])
        
    # Totals Row
    line_data.append(["", "", "Subtotal:", f"Rs {invoice.subtotal}"])
    line_data.append(["", "", "Tax Amount:", f"Rs {invoice.tax_amount}"])
    line_data.append(["", "", "Total Amount:", f"Rs {invoice.total_amount}"])
    
    t_lines = Table(line_data, colWidths=[4*inch, 0.75*inch, 1.25*inch, 1.25*inch])
    t_lines.setStyle(TableStyle([
        # Header Row
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3b82f6")), # Tailwind blue-500
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('TOPPADDING', (0,0), (-1,0), 12),
        
        # Grid for items
        ('GRID', (0,1), (-1,-4), 1, colors.HexColor("#E5E7EB")),
        ('BOTTOMPADDING', (0,1), (-1,-4), 8),
        ('TOPPADDING', (0,1), (-1,-4), 8),
        
        # Alignments
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        
        # Totals Formatting
        ('FONTNAME', (2,-3), (2,-1), 'Helvetica-Bold'),
        ('FONTNAME', (3,-3), (3,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (2,-1), (-1,-1), 2, colors.HexColor("#3b82f6")), # Double line for final total
        ('BOTTOMPADDING', (2,-3), (-1,-1), 6),
        ('TOPPADDING', (2,-3), (-1,-1), 6),
    ]))
    
    elements.append(t_lines)
    
    doc.build(elements)
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f"Invoice_{invoice.invoice_number}.pdf")
