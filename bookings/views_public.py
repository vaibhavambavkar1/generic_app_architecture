from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
import datetime
from .models import BusinessProfile, Resource
from .forms import CustomerForm
from .services.slot_engine import SlotEngine
from .services.booking_service import BookingService

def public_booking(request):
    """
    Public-facing view where unauthenticated users can select resources,
    see available slots, and book.
    Uses the request.tenant set by TenantMiddleware.
    """
    business = getattr(request, 'tenant', None)
    if not business:
        return render(request, 'core/error.html', {'message': 'Business profile not found.'})
        
    resources = Resource.objects.filter(business=business, is_active=True)
    today_str = timezone.now().date().strftime('%Y-%m-%d')
    
    return render(request, 'bookings/public/calendar.html', {
        'business': business, 
        'resources': resources, 
        'today_str': today_str
    })

def public_api_slots(request):
    """Public version of the HTMX slots endpoint."""
    business = getattr(request, 'tenant', None)
    date_str = request.GET.get('date')
    resource_id = request.GET.get('resource_id')
    
    if not date_str or not resource_id or not business:
        return render(request, 'bookings/calendar/_slots_public.html', {'error': 'Missing details.'})
        
    try:
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        resource = Resource.objects.get(id=resource_id, business=business)
    except (ValueError, Resource.DoesNotExist):
        return render(request, 'bookings/calendar/_slots_public.html', {'error': 'Invalid data.'})
        
    slots = SlotEngine.get_available_slots(business, resource, target_date)
    return render(request, 'bookings/calendar/_slots_public.html', {
        'slots': slots, 'date': target_date, 'resource': resource, 'business': business
    })

def public_checkout(request):
    business = getattr(request, 'tenant', None)
    if not business:
        return redirect('/')
        
    # Get parameters from calendar picker or post
    resource_id = request.GET.get('resource_id') or request.POST.get('resource_id')
    date_str = request.GET.get('date') or request.POST.get('date')
    selected_slot = request.GET.get('selected_slot') or request.POST.get('selected_slot')
    
    if not resource_id or not date_str:
        messages.error(request, 'Missing booking details. Please start from the calendar.')
        return redirect('bookings:public_booking')
        
    resource = get_object_or_404(Resource, id=resource_id, business=business)
    target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    
    if business.industry.config.get('slot_mode') == 'date_range':
        start_dt = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(14, 0)))
        end_dt = start_dt + datetime.timedelta(days=1)
    else:
        if not selected_slot:
            messages.error(request, 'Please select a specific time slot.')
            return redirect('bookings:public_booking')
            
        slot_time = datetime.datetime.strptime(selected_slot, '%H:%M').time()
        start_dt = timezone.make_aware(datetime.datetime.combine(target_date, slot_time))
        duration_mins = resource.resource_type.default_duration_minutes or 60
        end_dt = start_dt + datetime.timedelta(minutes=duration_mins)

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            from .models import Customer
            customer, _ = Customer.objects.get_or_create(
                business=business,
                email=form.cleaned_data['email'],
                defaults={'name': form.cleaned_data['name'], 'phone': form.cleaned_data['phone']}
            )
            
            try:
                booking = BookingService.create_booking(
                    business=business,
                    customer=customer,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    items=[{"resource": resource, "quantity": 1}],
                    slot_mode=business.industry.config.get('slot_mode', 'time_slot'),
                    source='ONLINE'
                )
                
                # In a real app we'd redirect to payment gateway here.
                # Since we don't have one, we show success page.
                return render(request, 'bookings/public/success.html', {'booking': booking})
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
    else:
        form = CustomerForm()

    context = {
        'business': business,
        'resource': resource,
        'date': target_date,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'form': form
    }
    return render(request, 'bookings/public/checkout.html', context)
