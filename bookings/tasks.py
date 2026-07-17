import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Booking
from .services.booking_service import BookingService

logger = logging.getLogger(__name__)

@shared_task
def send_booking_reminders():
    """
    Sends reminders for bookings that are coming up within the next 24 hours.
    """
    now = timezone.now()
    reminder_window = now + timedelta(hours=24)
    
    # Get confirmed bookings starting in the next 24 hours
    upcoming_bookings = Booking.objects.filter(
        status='Confirmed',
        start_datetime__gt=now,
        start_datetime__lte=reminder_window
    )
    
    count = 0
    for booking in upcoming_bookings:
        # In a real app, check if a reminder was already sent
        # and send an email/SMS using customer details.
        logger.info(f"Sent reminder for booking {booking.booking_number} to {booking.customer.email}")
        count += 1
        
    return f"Sent {count} reminders."

@shared_task
def auto_cancel_unpaid_drafts():
    """
    Cancels drafts or pending bookings that have been sitting for too long without confirmation.
    """
    timeout = timezone.now() - timedelta(minutes=30)
    stale_bookings = Booking.objects.filter(
        status__in=['Draft', 'Pending'],
        created_at__lte=timeout
    )
    
    count = 0
    for booking in stale_bookings:
        try:
            BookingService.cancel_booking(booking, user=None)
            booking.save()
            count += 1
            logger.info(f"Auto-cancelled unpaid/pending booking {booking.booking_number}")
        except Exception as e:
            logger.error(f"Failed to auto-cancel {booking.booking_number}: {e}")
            
    return f"Auto-cancelled {count} stale bookings."

@shared_task
def process_no_shows():
    """
    Marks confirmed bookings as 'NoShow' if they missed their check-in window (e.g., 2 hours past start).
    """
    cutoff = timezone.now() - timedelta(hours=2)
    no_shows = Booking.objects.filter(
        status='Confirmed',
        start_datetime__lte=cutoff
    )
    
    count = 0
    for booking in no_shows:
        try:
            booking.mark_no_show()
            booking.save()
            count += 1
            logger.info(f"Marked {booking.booking_number} as No-Show")
        except Exception as e:
            logger.error(f"Failed to mark no-show for {booking.booking_number}: {e}")
            
    return f"Marked {count} no-shows."
