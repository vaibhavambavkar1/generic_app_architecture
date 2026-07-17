import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import Organization
from .models import BusinessProfile, Resource, OperatingSchedule, Booking, Customer
from .forms import BusinessSetupForm, ResourceForm, OperatingScheduleForm, CustomerForm
from .services.slot_engine import SlotEngine
from .services.booking_service import BookingService
from django.contrib import messages

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

@login_required
def booking_create(request):
    """Handles submission from the calendar picker to create a booking."""
    business = get_business(request)
    if not business:
        return redirect('bookings:setup_wizard')
        
    # Get parameters from calendar picker or post
    resource_id = request.GET.get('resource_id') or request.POST.get('resource_id')
    date_str = request.GET.get('date') or request.POST.get('date')
    selected_slot = request.GET.get('selected_slot') or request.POST.get('selected_slot')
    
    if not resource_id or not date_str:
        messages.error(request, 'Missing booking details. Please start from the calendar.')
        return redirect('bookings:calendar')
        
    resource = get_object_or_404(Resource, id=resource_id, business=business)
    target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Calculate start and end datetimes
    if business.industry.config.get('slot_mode') == 'date_range':
        # Default duration for date_range is typically 1 day (e.g., hotel)
        start_dt = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(14, 0))) # standard checkin
        end_dt = start_dt + datetime.timedelta(days=1)
    else:
        if not selected_slot:
            messages.error(request, 'Please select a specific time slot.')
            return redirect('bookings:calendar')
            
        slot_time = datetime.datetime.strptime(selected_slot, '%H:%M').time()
        start_dt = timezone.make_aware(datetime.datetime.combine(target_date, slot_time))
        # duration
        duration_mins = resource.resource_type.default_duration_minutes or 60
        end_dt = start_dt + datetime.timedelta(minutes=duration_mins)

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer, _ = Customer.objects.get_or_create(
                business=business,
                email=form.cleaned_data['email'],
                defaults={'name': form.cleaned_data['name'], 'phone': form.cleaned_data['phone'], 'user': request.user}
            )
            
            try:
                booking = BookingService.create_booking(
                    business=business,
                    customer=customer,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    items=[{"resource": resource, "quantity": 1}],
                    slot_mode=business.industry.config.get('slot_mode', 'time_slot')
                )
                messages.success(request, f'Booking {booking.booking_number} created successfully!')
                # Return HTMX response with trigger and redirect
                import json
                from django.http import HttpResponse
                from django.urls import reverse
                
                response = HttpResponse()
                response['HX-Redirect'] = reverse('bookings:booking_detail', kwargs={'pk': booking.pk})
                response['HX-Trigger'] = json.dumps({
                    "showReceiptPrompt": {"url": reverse('bookings:booking_receipt_pdf', kwargs={'pk': booking.pk})}
                })
                return response
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
    else:
        form = CustomerForm(initial={'name': request.user.get_full_name(), 'email': request.user.email})

    context = {
        'business': business,
        'resource': resource,
        'date': target_date,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'form': form
    }
    return render(request, 'bookings/booking_create.html', context)

@login_required
def booking_detail(request, pk):
    business = get_business(request)
    booking = get_object_or_404(Booking, pk=pk, business=business)
    return render(request, 'bookings/booking_detail.html', {'booking': booking, 'business': business})

@login_required
def booking_action(request, pk, action):
    """HTMX endpoint for state machine transitions"""
    business = get_business(request)
    booking = get_object_or_404(Booking, pk=pk, business=business)
    
    if request.method == 'POST':
        try:
            if action == 'confirm':
                booking.confirm()
            elif action == 'check_in':
                booking.check_in()
            elif action == 'complete':
                booking.complete()
            elif action == 'no_show':
                booking.no_show()
            elif action == 'cancel':
                BookingService.cancel_booking(booking, user=request.user)
            else:
                return render(request, 'bookings/components/_booking_actions.html', {'booking': booking, 'error': 'Invalid action'})
                
            booking.save()
            return render(request, 'bookings/components/_booking_actions.html', {'booking': booking})
            
        except Exception as e:
             return render(request, 'bookings/components/_booking_actions.html', {'booking': booking, 'error': str(e)})

    return render(request, 'bookings/components/_booking_actions.html', {'booking': booking})

