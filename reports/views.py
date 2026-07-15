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

    context = {
        'revenue_30d': revenue_30d,
        'total_payables': total_payables,
        'total_inventory_value': total_inventory_value,
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
