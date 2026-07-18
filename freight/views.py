from django.shortcuts import render, get_object_or_404
from .models import FreightBooking

def freight_tracking(request, booking_number):
    booking = get_object_or_404(FreightBooking, booking_number=booking_number)
    
    # Pre-fetch related data for the template
    legs = booking.legs.all().order_by('sequence')
    
    context = {
        'booking': booking,
        'legs': legs,
        'has_bol': hasattr(booking, 'bol'),
        'has_awb': hasattr(booking, 'awb'),
        'has_customs': hasattr(booking, 'customs'),
    }
    return render(request, 'freight/tracking_dashboard.html', context)
