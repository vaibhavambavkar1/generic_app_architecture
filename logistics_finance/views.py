from django.shortcuts import render
from finance.models import JournalEntry, JournalEntryLine

def financial_dashboard(request):
    # Fetch AR related to logistics (Waybill, Freight, WMS)
    ar_lines = JournalEntryLine.objects.filter(
        account__code='1100'
    ).exclude(
        journal_entry__entry_number__startswith='JE-POS'
    ).exclude(
        journal_entry__entry_number__startswith='JE-INV'
    ).select_related('journal_entry', 'customer').order_by('-id')[:20]
    
    # Fetch AP related to logistics (Carriers)
    ap_lines = JournalEntryLine.objects.filter(
        account__code='2000',
        journal_entry__entry_number__startswith='JE-FRT-AP'
    ).select_related('journal_entry', 'supplier').order_by('-id')[:20]

    return render(request, 'logistics_finance/dashboard.html', {
        'ar_lines': ar_lines,
        'ap_lines': ap_lines,
    })
