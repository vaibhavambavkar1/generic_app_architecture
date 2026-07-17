import datetime
from django.db.models import Sum
from django.utils import timezone
from ..models import (
    BusinessProfile, Resource, OperatingSchedule, Holiday, SlotOverride, BookingItem
)


class SlotEngine:
    """
    Availability Slot Engine. Calculates operating windows, applies holiday/slot overrides,
    and checks overlaps against existing bookings to determine open slots.
    """

    @staticmethod
    def get_available_slots(business: BusinessProfile, resource: Resource, target_date: datetime.date) -> list[dict]:
        """
        Returns a list of slots for the given resource and date.
        Each slot contains start_time, end_time, and capacity_remaining.
        """
        # 1. Check Holidays
        if Holiday.objects.filter(business=business, date=target_date).exists():
            return []

        # 2. Check BLOCK Overrides
        block_overrides = SlotOverride.objects.filter(
            business=business,
            date=target_date,
            override_type='BLOCK'
        )
        if block_overrides.filter(resource=resource).exists() or block_overrides.filter(resource__isnull=True).exists():
            return []

        # 3. Determine Operating Hours for this day
        # Look for EXTEND overrides first
        extend_overrides = SlotOverride.objects.filter(
            business=business,
            date=target_date,
            override_type='EXTEND'
        )
        resource_override = extend_overrides.filter(resource=resource).first()
        general_override = extend_overrides.filter(resource__isnull=True).first()

        start_time = None
        end_time = None
        slot_duration = None
        max_concurrent = 1

        if resource_override:
            start_time = resource_override.start_time
            end_time = resource_override.end_time
        elif general_override:
            start_time = general_override.start_time
            end_time = general_override.end_time
        else:
            # Fallback to OperatingSchedule
            day_of_week = target_date.weekday()
            schedule = OperatingSchedule.objects.filter(
                business=business,
                day_of_week=day_of_week,
                is_active=True
            )
            # Prioritize resource-specific schedule, then fallback to general
            res_schedule = schedule.filter(resource=resource).first()
            gen_schedule = schedule.filter(resource__isnull=True).first()

            selected_schedule = res_schedule or gen_schedule
            if not selected_schedule:
                return []

            start_time = selected_schedule.start_time
            end_time = selected_schedule.end_time
            slot_duration = selected_schedule.slot_duration_minutes
            max_concurrent = selected_schedule.max_concurrent

        # Fallback for slot_duration if not set by override
        if slot_duration is None:
            slot_duration = resource.resource_type.default_duration_minutes

        slots = []
        if slot_duration:
            # Partition into fixed intervals
            current_dt = datetime.datetime.combine(target_date, start_time)
            end_dt = datetime.datetime.combine(target_date, end_time)
            duration_delta = datetime.timedelta(minutes=slot_duration)

            while current_dt + duration_delta <= end_dt:
                slot_start = current_dt.time()
                slot_end = (current_dt + duration_delta).time()
                slots.append({
                    "start_time": slot_start,
                    "end_time": slot_end,
                })
                current_dt += duration_delta
        else:
            # Return single flexible slot covering the entire operating hours
            slots.append({
                "start_time": start_time,
                "end_time": end_time,
            })

        # 4. Check existing bookings to calculate capacity
        final_slots = []
        for slot in slots:
            # Handle localized timezone correctly using project default timezone
            slot_start_dt = timezone.make_aware(datetime.datetime.combine(target_date, slot["start_time"]))
            slot_end_dt = timezone.make_aware(datetime.datetime.combine(target_date, slot["end_time"]))

            # Query bookings that overlap with this slot
            overlapping_bookings = BookingItem.objects.filter(
                resource=resource,
                booking__business=business,
                booking__status__in=['Pending', 'Confirmed', 'CheckedIn']
            ).filter(
                booking__start_datetime__lt=slot_end_dt,
                booking__end_datetime__gt=slot_start_dt
            ).aggregate(total_quantity=Sum('quantity'))

            booked_qty = overlapping_bookings['total_quantity'] or 0

            # Capacity check
            effective_capacity = min(resource.capacity, max_concurrent)
            capacity_remaining = max(0, effective_capacity - booked_qty)

            if capacity_remaining > 0:
                final_slots.append({
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "capacity_remaining": capacity_remaining
                })

        return final_slots

    @staticmethod
    def check_availability(business: BusinessProfile, resource: Resource, start_dt: datetime.datetime, end_dt: datetime.datetime, quantity: int = 1) -> bool:
        """
        Validates if the resource is available for the given quantity in the specific datetime window.
        """
        # Ensure timezone awareness
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)

        target_date = start_dt.date()

        # Check Holidays
        if Holiday.objects.filter(business=business, date=target_date).exists():
            return False

        # Check BLOCK Overrides
        block_overrides = SlotOverride.objects.filter(
            business=business,
            date=target_date,
            override_type='BLOCK'
        )
        if block_overrides.filter(resource=resource).exists() or block_overrides.filter(resource__isnull=True).exists():
            return False

        # Get existing bookings overlap sum
        overlapping_bookings = BookingItem.objects.filter(
            resource=resource,
            booking__business=business,
            booking__status__in=['Pending', 'Confirmed', 'CheckedIn']
        ).filter(
            booking__start_datetime__lt=end_dt,
            booking__end_datetime__gt=start_dt
        ).aggregate(total_quantity=Sum('quantity'))

        booked_qty = overlapping_bookings['total_quantity'] or 0

        return (booked_qty + quantity) <= resource.capacity
