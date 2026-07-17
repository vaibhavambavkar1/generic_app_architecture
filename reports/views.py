from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
import json

from sales.models import POSInvoice, SalesOrder
from purchasing.models import GoodsReceiptNote, StorePurchaseOrder
from finance.models import Account, AccountCategory
from generic_store_mgmt.models import Product
from inventory.models import StockLedger

@login_required
def executive_dashboard(request):
    """
    High-level overview combining Sales, Purchases, and Finance.
    """
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # 1. Total Revenue (Last 30 days) from POS
    revenue_30d = POSInvoice.objects.filter(is_paid=True, date__gte=thirty_days_ago).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # 2. Open Payables & Assets from Finance Accounts
    ap_account = Account.objects.filter(code='2000').first()
    inventory_account = Account.objects.filter(code='1200').first()
    
    total_payables = ap_account.balance if ap_account else 0
    total_inventory_value = inventory_account.balance if inventory_account else 0
    
    # 3. Chart Data: Last 7 Days Sales
    seven_days_ago = today - timedelta(days=7)
    recent_sales = POSInvoice.objects.filter(is_paid=True, date__gte=seven_days_ago) \
        .extra({'day': "date(date)"}) \
        .values('day') \
        .annotate(total=Sum('total_amount')) \
        .order_by('day')
        
    chart_labels = [str(s['day']) for s in recent_sales]
    chart_data = [float(s['total']) for s in recent_sales]

    # 4. Additional Widgets (Cash, AR, Pending, Low Stock, Top Products)
    cash_account = Account.objects.filter(code='1000').first()
    ar_account = Account.objects.filter(code='1100').first()
    total_cash = cash_account.balance if cash_account else 0
    total_receivables = ar_account.balance if ar_account else 0
    
    pending_approvals_count = StorePurchaseOrder.objects.filter(status='Submitted').count()
    
    # Low stock alerts from generic_store_mgmt or inventory. 
    # For now, let's just get some dummy top products since we don't have stock directly linked in generic product
    # Wait, POSInvoice uses generic_store_mgmt Product. InventoryItem is separate.
    # We will use top products from POSInvoice
    top_products = POSInvoice.objects.filter(is_paid=True, date__gte=thirty_days_ago).values(
        'lines__product__name'
    ).annotate(
        total_sold=Sum('lines__quantity'),
        total_revenue=Sum('lines__line_total')
    ).exclude(lines__product__name__isnull=True).order_by('-total_revenue')[:5]
    
    high_value_pos = StorePurchaseOrder.objects.filter(total_amount__gte=50000).order_by('-created_at')[:5]

    context = {
        'revenue_30d': revenue_30d,
        'total_payables': total_payables,
        'total_inventory_value': total_inventory_value,
        'total_cash': total_cash,
        'total_receivables': total_receivables,
        'pending_approvals_count': pending_approvals_count,
        'top_products': top_products,
        'high_value_pos': high_value_pos,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'reports/executive_dashboard.html', context)

@login_required
def sales_report(request):
    """Detailed Sales Report"""
    # Group by product
    top_products = POSInvoice.objects.filter(is_paid=True).values(
        product_name=F('lines__product__name')
    ).annotate(
        total_sold=Sum('lines__quantity'),
        total_revenue=Sum('lines__line_total')
    ).order_by('-total_revenue')[:10]
    
    return render(request, 'reports/sales_report.html', {'top_products': top_products})

@login_required
def inventory_report(request):
    """Current Stock Levels via Ledger Aggregation"""
    stock_levels = StockLedger.objects.values(
        product_name=F('product__name'),
        warehouse_name=F('warehouse__name')
    ).annotate(
        current_stock=Sum('quantity')
    ).order_by('product_name')
    
    return render(request, 'reports/inventory_report.html', {'stock_levels': stock_levels})

import csv
from django.http import HttpResponse
from finance.models import JournalEntryLine, JournalEntry

@login_required
def finance_reports_hub(request):
    return render(request, 'reports/finance_reports_hub.html')

@login_required
def trial_balance(request):
    accounts = Account.objects.all().order_by('code')
    
    tb_data = []
    total_debit = 0
    total_credit = 0
    
    for acc in accounts:
        if acc.balance == 0:
            continue
            
        debit_bal = 0
        credit_bal = 0
        
        if acc.category in [AccountCategory.ASSET, AccountCategory.EXPENSE]:
            if acc.balance > 0:
                debit_bal = acc.balance
            else:
                credit_bal = abs(acc.balance)
        else:
            if acc.balance > 0:
                credit_bal = acc.balance
            else:
                debit_bal = abs(acc.balance)
                
        tb_data.append({
            'code': acc.code,
            'name': acc.name,
            'debit': debit_bal,
            'credit': credit_bal
        })
        total_debit += debit_bal
        total_credit += credit_bal
        
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="trial_balance.csv"'
        writer = csv.writer(response)
        writer.writerow(['Account Code', 'Account Name', 'Debit', 'Credit'])
        for row in tb_data:
            writer.writerow([row['code'], row['name'], row['debit'] if row['debit'] else '', row['credit'] if row['credit'] else ''])
        writer.writerow(['', 'TOTAL', total_debit, total_credit])
        return response

    context = {
        'tb_data': tb_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
    }
    return render(request, 'reports/trial_balance.html', context)

@login_required
def general_ledger(request):
    account_id = request.GET.get('account')
    lines = None
    selected_acc = None
    
    if account_id:
        from django.shortcuts import get_object_or_404
        selected_acc = get_object_or_404(Account, pk=account_id)
        lines = JournalEntryLine.objects.filter(account=selected_acc, journal_entry__is_posted=True).order_by('journal_entry__date', 'id')
        
        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="gl_{selected_acc.code}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Date', 'Entry #', 'Reference', 'Description', 'Debit', 'Credit'])
            for line in lines:
                writer.writerow([
                    line.journal_entry.date,
                    line.journal_entry.entry_number,
                    line.journal_entry.reference,
                    line.description,
                    line.debit,
                    line.credit
                ])
            return response
            
    accounts = Account.objects.all().order_by('code')
    return render(request, 'reports/general_ledger.html', {'accounts': accounts, 'lines': lines, 'selected_acc': selected_acc})

@login_required
def income_statement(request):
    revenues = Account.objects.filter(category=AccountCategory.REVENUE)
    expenses = Account.objects.filter(category=AccountCategory.EXPENSE)
    
    rev_data = [{'code': r.code, 'name': r.name, 'balance': r.balance} for r in revenues if r.balance != 0]
    exp_data = [{'code': e.code, 'name': e.name, 'balance': e.balance} for e in expenses if e.balance != 0]
    
    total_rev = sum(r['balance'] for r in rev_data)
    total_exp = sum(e['balance'] for e in exp_data)
    net_income = total_rev - total_exp
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="income_statement.csv"'
        writer = csv.writer(response)
        writer.writerow(['Type', 'Account Code', 'Account Name', 'Balance'])
        for r in rev_data:
            writer.writerow(['Revenue', r['code'], r['name'], r['balance']])
        writer.writerow(['', '', 'Total Revenue', total_rev])
        writer.writerow([])
        for e in exp_data:
            writer.writerow(['Expense', e['code'], e['name'], e['balance']])
        writer.writerow(['', '', 'Total Expense', total_exp])
        writer.writerow([])
        writer.writerow(['', '', 'Net Income', net_income])
        return response
        
    context = {
        'revenues': rev_data,
        'expenses': exp_data,
        'total_rev': total_rev,
        'total_exp': total_exp,
        'net_income': net_income
    }
    return render(request, 'reports/income_statement.html', context)

@login_required
def balance_sheet(request):
    assets = Account.objects.filter(category=AccountCategory.ASSET)
    liabilities = Account.objects.filter(category=AccountCategory.LIABILITY)
    equity = Account.objects.filter(category=AccountCategory.EQUITY)
    
    asset_data = [{'code': a.code, 'name': a.name, 'balance': a.balance} for a in assets if a.balance != 0]
    liab_data = [{'code': l.code, 'name': l.name, 'balance': l.balance} for l in liabilities if l.balance != 0]
    equity_data = [{'code': e.code, 'name': e.name, 'balance': e.balance} for e in equity if e.balance != 0]
    
    total_assets = sum(a['balance'] for a in asset_data)
    total_liab = sum(l['balance'] for l in liab_data)
    total_equity = sum(e['balance'] for e in equity_data)
    
    revenues = Account.objects.filter(category=AccountCategory.REVENUE)
    expenses = Account.objects.filter(category=AccountCategory.EXPENSE)
    net_income = sum(r.balance for r in revenues) - sum(e.balance for e in expenses)
    
    if net_income != 0:
        equity_data.append({'code': '-', 'name': 'Current Year Net Income', 'balance': net_income})
        total_equity += net_income
        
    total_liab_equity = total_liab + total_equity
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="balance_sheet.csv"'
        writer = csv.writer(response)
        writer.writerow(['Category', 'Account Code', 'Account Name', 'Balance'])
        for a in asset_data:
            writer.writerow(['Asset', a['code'], a['name'], a['balance']])
        writer.writerow(['', '', 'Total Assets', total_assets])
        writer.writerow([])
        for l in liab_data:
            writer.writerow(['Liability', l['code'], l['name'], l['balance']])
        writer.writerow(['', '', 'Total Liabilities', total_liab])
        writer.writerow([])
        for e in equity_data:
            writer.writerow(['Equity', e['code'], e['name'], e['balance']])
        writer.writerow(['', '', 'Total Equity', total_equity])
        writer.writerow([])
        writer.writerow(['', '', 'Total Liabilities & Equity', total_liab_equity])
        return response

    context = {
        'assets': asset_data,
        'liabilities': liab_data,
        'equity': equity_data,
        'total_assets': total_assets,
        'total_liab': total_liab,
        'total_equity': total_equity,
        'total_liab_equity': total_liab_equity
    }
    return render(request, 'reports/balance_sheet.html', context)
