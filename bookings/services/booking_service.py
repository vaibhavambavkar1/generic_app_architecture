from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import Booking, BookingItem, BookingAddon, Customer, BusinessProfile
from .slot_engine import SlotEngine
from .pricing_engine import PricingEngine


class BookingService:
    """
    Orchestration layer to handle the booking lifecycle: Create, Reschedule, Cancel, Check-in, Check-out.
    Enforces ACID transactions and business configuration rules.
    """

    @staticmethod
    @transaction.atomic
    def create_booking(
        business: BusinessProfile,
        customer: Customer,
        start_dt: timezone.datetime,
        end_dt: timezone.datetime,
        items: list[dict],  # list of {"resource": Resource, "quantity": int}
        addons: list[dict] = None,  # list of {"addon": Addon, "quantity": int}
        slot_mode: str = 'time_slot',
        custom_data: dict = None,
        notes: str = '',
        source: str = 'WALK_IN'
    ) -> Booking:
        """
        Atomically validates, calculates prices, and creates a Booking with items and addons.
        """
        if not items:
            raise ValidationError("A booking must include at least one resource item.")

        # 1. Validate availability for all items
        for item in items:
            resource = item["resource"]
            qty = item.get("quantity", 1)

            # Ensure resource belongs to business
            if resource.business != business:
                raise ValidationError(f"Resource {resource.name} does not belong to this business.")

            is_available = SlotEngine.check_availability(
                business=business,
                resource=resource,
                start_dt=start_dt,
                end_dt=end_dt,
                quantity=qty
            )
            if not is_available:
                raise ValidationError(f"Resource '{resource.name}' is not available for the selected slot.")

        # 2. Create the Booking object in 'Draft' FSM state
        booking = Booking(
            business=business,
            customer=customer,
            slot_mode=slot_mode,
            start_datetime=start_dt,
            end_datetime=end_dt,
            custom_data=custom_data or {},
            notes=notes,
            source=source
        )
        booking.save()

        subtotal = 0.00
        tax_amount = 0.00
        discount_amount = 0.00
        total_amount = 0.00

        # 3. Create BookingItems & calculate their pricing
        for item in items:
            resource = item["resource"]
            qty = item.get("quantity", 1)

            # Compute pricing breakdown
            pricing = PricingEngine.calculate_price(
                business=business,
                resource=resource,
                start_dt=start_dt,
                end_dt=end_dt,
                quantity=qty,
                addons=None
            )

            # Add to main totals
            subtotal += float(pricing["subtotal"])
            tax_amount += float(pricing["tax_amount"])
            discount_amount += float(pricing["discount_amount"])
            total_amount += float(pricing["total_amount"])

            # Create line item
            BookingItem.objects.create(
                booking=booking,
                resource=resource,
                quantity=qty,
                unit_price=pricing["unit_price"],
                line_total=pricing["subtotal"]
            )

        # 4. Create BookingAddons if present
        if addons:
            for addon_item in addons:
                addon = addon_item["addon"]
                qty = addon_item.get("quantity", 1)

                if addon.business != business:
                    raise ValidationError(f"Add-on {addon.name} does not belong to this business.")

                line_total = addon.price * qty
                subtotal += float(line_total)
                total_amount += float(line_total)

                BookingAddon.objects.create(
                    booking=booking,
                    addon=addon,
                    quantity=qty,
                    unit_price=addon.price,
                    line_total=line_total
                )

        # Update totals back to booking
        booking.subtotal = subtotal
        booking.tax_amount = tax_amount
        booking.discount_amount = discount_amount
        booking.total_amount = total_amount
        booking.save()

        # 5. Automatically transition based on configuration (default: Confirmed)
        requires_approval = business.get_config('requires_approval', False)
        if requires_approval:
            booking.submit_pending()
        else:
            booking.confirm()
        booking.save()

        return booking

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking: Booking, user=None) -> Booking:
        """
        Transition booking to CANCELLED state and free up resource slots.
        """
        if user:
            booking._audit_user_id = user.id

        booking.cancel()
        booking.save()
        return booking

    @staticmethod
    @transaction.atomic
    def reschedule_booking(booking: Booking, new_start_dt: timezone.datetime, new_end_dt: timezone.datetime, user=None) -> Booking:
        """
        Validates availability for the new window, updates start/end time, and recalculates pricing.
        """
        business = booking.business
        items = booking.items.all()

        # Validate availability in new window
        for item in items:
            is_available = SlotEngine.check_availability(
                business=business,
                resource=item.resource,
                start_dt=new_start_dt,
                end_dt=new_end_dt,
                quantity=item.quantity
            )
            if not is_available:
                raise ValidationError(f"Resource '{item.resource.name}' is not available for the rescheduled slot.")

        if user:
            booking._audit_user_id = user.id

        # Update booking details
        booking.start_datetime = new_start_dt
        booking.end_datetime = new_end_dt

        # Recalculate totals
        subtotal = 0.00
        tax_amount = 0.00
        discount_amount = 0.00
        total_amount = 0.00

        for item in items:
            pricing = PricingEngine.calculate_price(
                business=business,
                resource=item.resource,
                start_dt=new_start_dt,
                end_dt=new_end_dt,
                quantity=item.quantity
            )
            subtotal += float(pricing["subtotal"])
            tax_amount += float(pricing["tax_amount"])
            discount_amount += float(pricing["discount_amount"])
            total_amount += float(pricing["total_amount"])

            item.unit_price = pricing["unit_price"]
            item.line_total = pricing["subtotal"]
            item.save()

        # Recalculate addons (time invariant, but must be added to subtotal/total)
        for addon_item in booking.addons.all():
            subtotal += float(addon_item.line_total)
            total_amount += float(addon_item.line_total)

        booking.subtotal = subtotal
        booking.tax_amount = tax_amount
        booking.discount_amount = discount_amount
        booking.total_amount = total_amount
        booking.save()

        return booking
