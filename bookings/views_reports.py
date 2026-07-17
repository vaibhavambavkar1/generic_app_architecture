import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import plotly.express as px
import plotly.utils
from .models import Booking
from .views import get_business

@login_required
def reports_dashboard(request):
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
        
    thirty_days_ago = timezone.now() - timedelta(days=30)
    base_qs = Booking.objects.filter(business=business, created_at__gte=thirty_days_ago)
    
    # 1. Revenue over time (Confirmed, CheckedIn, Completed)
    revenue_data = base_qs.filter(
        status__in=['Confirmed', 'CheckedIn', 'Completed']
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total_revenue=Sum('total_amount')
    ).order_by('date')
    
    dates_rev = [item['date'].strftime('%Y-%m-%d') for item in revenue_data]
    revs = [float(item['total_revenue']) for item in revenue_data]
    
    if not dates_rev:
        dates_rev = [timezone.now().strftime('%Y-%m-%d')]
        revs = [0.0]
    
    fig_rev = px.line(x=dates_rev, y=revs, labels={'x': 'Date', 'y': f'Revenue ({business.currency})'}, title='30-Day Revenue Trend')
    fig_rev.update_traces(line_color='#3b82f6')
    rev_chart_json = json.dumps(fig_rev, cls=plotly.utils.PlotlyJSONEncoder)
    
    # 2. Occupancy / Bookings per Resource
    resource_data = base_qs.exclude(status='Cancelled').values('items__resource__name').annotate(
        booking_count=Count('id')
    ).order_by('-booking_count')
    
    res_names = [item['items__resource__name'] for item in resource_data if item['items__resource__name']]
    res_counts = [item['booking_count'] for item in resource_data if item['items__resource__name']]
    
    if not res_names:
        res_names = ['No Data']
        res_counts = [0]
    
    fig_occ = px.bar(x=res_names, y=res_counts, labels={'x': 'Resource', 'y': 'Total Bookings'}, title='Resource Popularity')
    fig_occ.update_traces(marker_color='#10b981')
    occ_chart_json = json.dumps(fig_occ, cls=plotly.utils.PlotlyJSONEncoder)
    
    # 3. Status/Cancellation Analytics
    status_data = base_qs.values('status').annotate(count=Count('id'))
    statuses = [item['status'] for item in status_data]
    counts = [item['count'] for item in status_data]
    
    if not statuses:
        statuses = ['No Data']
        counts = [1]
    
    fig_stat = px.pie(names=statuses, values=counts, title='Booking Status Breakdown', hole=0.4)
    stat_chart_json = json.dumps(fig_stat, cls=plotly.utils.PlotlyJSONEncoder)
    
    context = {
        'business': business,
        'rev_chart_json': rev_chart_json,
        'occ_chart_json': occ_chart_json,
        'stat_chart_json': stat_chart_json,
    }
    
    return render(request, 'bookings/reports.html', context)
