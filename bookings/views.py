import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import Organization
from .models import BusinessProfile, Resource, OperatingSchedule, Booking
from .forms import BusinessSetupForm, ResourceForm, OperatingScheduleForm
from .services.slot_engine import SlotEngine

@login_required
def get_business(request):
    """Helper to get the user's business profile or None"""
    org = Organization.objects.first() # Simplification for single org
    if not org:
        return None
    return BusinessProfile.objects.filter(organization=org).first()

@login_required
def dashboard(request):
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
    
    # Stats
    today = timezone.now().date()
    today_bookings = Booking.objects.filter(business=business, start_datetime__date=today).count()
    active_resources = Resource.objects.filter(business=business, is_active=True).count()
    recent_bookings = Booking.objects.filter(business=business).order_by('-start_datetime')[:5]
    
    context = {
        'business': business,
        'today_bookings': today_bookings,
        'active_resources': active_resources,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'bookings/dashboard.html', context)

@login_required
def setup_wizard(request):
    org = Organization.objects.first()
    if not org:
        # In a real app, this might redirect to create an org first
        org = Organization.objects.create(name="Default Org", owner_name=request.user.get_full_name(), email=request.user.email)

    business = BusinessProfile.objects.filter(organization=org).first()
    
    if request.method == 'POST':
        form = BusinessSetupForm(request.POST, instance=business)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.organization = org
            profile.save()
            return redirect('bookings:dashboard')
    else:
        form = BusinessSetupForm(instance=business)
        
    return render(request, 'bookings/wizard.html', {'form': form, 'business': business})

@login_required
def resource_list(request):
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
    resources = Resource.objects.filter(business=business)
    return render(request, 'bookings/resources/list.html', {'resources': resources, 'business': business})

@login_required
def resource_create(request):
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
    if request.method == 'POST':
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.business = business
            resource.save()
            return redirect('bookings:resource_list')
    else:
        form = ResourceForm()
        form.fields['resource_type'].queryset = form.fields['resource_type'].queryset.filter(business=business)
    return render(request, 'bookings/resources/form.html', {'form': form, 'title': 'Add Resource', 'business': business})

@login_required
def schedule_list(request):
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
    schedules = OperatingSchedule.objects.filter(business=business).order_by('day_of_week')
    return render(request, 'bookings/schedules/list.html', {'schedules': schedules, 'business': business})

@login_required
def schedule_create(request):
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
    if request.method == 'POST':
        form = OperatingScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.business = business
            schedule.save()
            return redirect('bookings:schedule_list')
    else:
        form = OperatingScheduleForm()
        # Filter resource dropdown to business
        form.fields['resource'].queryset = Resource.objects.filter(business=business)
    return render(request, 'bookings/schedules/form.html', {'form': form, 'title': 'Add Schedule', 'business': business})

@login_required
def calendar_view(request):
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
    resources = Resource.objects.filter(business=business, is_active=True)
    today_str = timezone.now().date().strftime('%Y-%m-%d')
    return render(request, 'bookings/calendar/picker.html', {'business': business, 'resources': resources, 'today_str': today_str})

@login_required
def api_slots(request):
    """HTMX endpoint to return available slots for a given date and resource."""
    business = get_business(request)
    date_str = request.GET.get('date')
    resource_id = request.GET.get('resource_id')
    
    if not date_str or not resource_id:
        return render(request, 'bookings/calendar/_slots.html', {'error': 'Missing date or resource'})
        
    try:
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        resource = Resource.objects.get(id=resource_id, business=business)
    except (ValueError, Resource.DoesNotExist):
        return render(request, 'bookings/calendar/_slots.html', {'error': 'Invalid data'})
        
    slots = SlotEngine.get_available_slots(business, resource, target_date)
    return render(request, 'bookings/calendar/_slots.html', {'slots': slots, 'date': target_date, 'resource': resource, 'business': business})
