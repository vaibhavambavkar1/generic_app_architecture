import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django_fsm import transition

from core.mixins import AuditableMixin
from core.models import WorkflowMixin, Organization

User = get_user_model()


class IndustryPreset(AuditableMixin):
    """
    Seed/Pre-configured template config for each booking vertical.
    Enables configuration-driven behavior for 26+ industries.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Industry Name")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    icon = models.CharField(max_length=50, help_text="FontAwesome/Icon name", blank=True)
    config = models.JSONField(
        default=dict,
        help_text="Configuration JSON defining labels, slot modes, constraints, and custom form fields."
    )

    class Meta:
        verbose_name = "Industry Preset"
        verbose_name_plural = "Industry Presets"

    def __str__(self) -> str:
        return self.name


class BusinessProfile(AuditableMixin):
    """
    A tenant's specific booking profile.
    Connects the system's single Organization to a selected IndustryPreset.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="booking_profiles")
    industry = models.ForeignKey(IndustryPreset, on_delete=models.PROTECT, related_name="business_profiles")
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    config_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text="Override defaults from the IndustryPreset."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Business Profile"
        verbose_name_plural = "Business Profiles"

    def get_config(self, key: str, default=None):
        """
        Retrieves a merged configuration key, prioritizing business overrides,
        then industry preset configs, and finally a default value.
        """
        if key in self.config_overrides:
            return self.config_overrides[key]
        if self.industry and key in self.industry.config:
            return self.industry.config[key]
        return default

    def __str__(self) -> str:
        return f"{self.name} ({self.industry.name})"


class ResourceType(AuditableMixin):
    """
    Categorizes resources (e.g., 'Deluxe Suite', 'OPD Clinic Room', 'Sedan Car').
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="resource_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    default_capacity = models.PositiveIntegerField(default=1)
    default_duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Default duration in minutes for time slot booking.")
    attributes_schema = models.JSONField(
        default=list,
        blank=True,
        help_text="Defines required custom attributes for resources of this type. E.g., [{'name': 'floor', 'type': 'int'}]"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Resource Type"
        verbose_name_plural = "Resource Types"

    def __str__(self) -> str:
        return f"{self.name} - {self.business.name}"


class Resource(AuditableMixin):
    """
    A single bookable unit (e.g. 'Room 101', 'Doctor John', 'Table #4', 'Audi A4 MH12').
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE, related_name="resources")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=1)
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom key-value pairs matching resource_type's attributes_schema."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('business', 'code')
        indexes = [
            models.Index(fields=['business', 'resource_type', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class OperatingSchedule(AuditableMixin):
    """
    Weekly operating template defining availability schedule for business profiles or specific resources.
    """
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="operating_schedules")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, null=True, blank=True, related_name="operating_schedules")
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="If null, bookable for flexible custom time ranges.")
    max_concurrent = models.PositiveIntegerField(default=1, help_text="Max bookings allowed at the same time slot for this schedule.")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Operating Schedule"
        verbose_name_plural = "Operating Schedules"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self) -> str:
        target = self.resource.name if self.resource else "General Business"
        return f"{target} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"


class Holiday(AuditableMixin):
    """
    Blocked dates for the entire business, meaning no bookings can be made.
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="holidays")
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('business', 'date')

    def __str__(self) -> str:
        return f"{self.business.name} - Holiday on {self.date} ({self.reason})"


class SlotOverride(AuditableMixin):
    """
    Specific overrides for availability on a particular date.
    Can block dates or extend/reduce operating hours.
    """
    OVERRIDE_TYPES = (
        ('BLOCK', 'Block completely'),
        ('EXTEND', 'Modify/Extend Hours'),
    )
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="slot_overrides")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, null=True, blank=True, related_name="slot_overrides")
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True, help_text="Required if override type is EXTEND.")
    end_time = models.TimeField(null=True, blank=True, help_text="Required if override type is EXTEND.")
    override_type = models.CharField(max_length=10, choices=OVERRIDE_TYPES, default='BLOCK')

    class Meta:
        verbose_name = "Slot Override"
        verbose_name_plural = "Slot Overrides"

    def clean(self):
        if self.override_type == 'EXTEND':
            if not self.start_time or not self.end_time:
                raise ValidationError("Start and end times are required to extend/modify hours.")
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time.")

    def __str__(self) -> str:
        target = self.resource.name if self.resource else "General Business"
        return f"{target} override on {self.date} ({self.get_override_type_display()})"


class Customer(AuditableMixin):
    """
    Decoupled Customer profile supporting both user-registered logins and anonymous guest details.
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="customers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="booking_customers")
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    metadata = models.JSONField(default=dict, blank=True, help_text="Custom customer preferences, history, or CRM attributes.")

    class Meta:
        unique_together = ('business', 'phone')

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class Booking(WorkflowMixin):
    """
    Represents the actual Reservation / Appointment / Booking record.
    Integrates with Core's WorkflowMixin (FSM state machine) and AuditableMixin.
    """
    SLOT_MODES = (
        ('time_slot', 'Time Slot'),
        ('date_range', 'Date Range'),
        ('recurring', 'Recurring'),
    )
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="bookings")
    booking_number = models.CharField(max_length=30, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="bookings")
    
    slot_mode = models.CharField(max_length=20, choices=SLOT_MODES)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dynamically structured fields dictated by the IndustryPreset custom fields."
    )
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=20, default='WALK_IN')  # WALK_IN, ONLINE, PHONE, API

    class Meta:
        indexes = [
            models.Index(fields=['business', 'status']),
            models.Index(fields=['business', 'start_datetime']),
            models.Index(fields=['customer']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_number:
            self.booking_number = f"BK-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    # -------------------------------------------------------------------------
    # FSM State Transitions
    # -------------------------------------------------------------------------
    @transition(field='status', source='Draft', target='Pending')
    def submit_pending(self) -> None:
        """Submit the booking for confirmation/payment processing."""
        pass

    @transition(field='status', source=['Draft', 'Pending'], target='Confirmed')
    def confirm(self) -> None:
        """Confirm the booking."""
        pass

    @transition(field='status', source='Confirmed', target='CheckedIn')
    def check_in(self) -> None:
        """Check in customer / occupy resource."""
        pass

    @transition(field='status', source='CheckedIn', target='Completed')
    def complete(self) -> None:
        """Complete/checkout booking."""
        pass

    @transition(field='status', source=['Draft', 'Pending', 'Confirmed'], target='Cancelled')
    def cancel(self) -> None:
        """Cancel booking."""
        pass

    @transition(field='status', source='Confirmed', target='NoShow')
    def mark_no_show(self) -> None:
        """Mark confirmed customer as No Show."""
        pass

    def __str__(self) -> str:
        return f"{self.booking_number} ({self.status})"


class BookingItem(AuditableMixin):
    """
    Reservations linked to specific bookable Resources.
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="items")
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name="booking_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def clean(self):
        if self.quantity > self.resource.capacity:
            raise ValidationError(f"Quantity exceeds the resource's capacity of {self.resource.capacity}.")

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.resource.name} x {self.quantity} for {self.booking.booking_number}"


class Addon(AuditableMixin):
    """
    Extra services/goods catalog bookable alongside resources (e.g., 'Spa Massage', 'Airport pickup', 'Projector Rental').
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="addons")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} (${self.price})"


class BookingAddon(AuditableMixin):
    """
    Optional add-ons added to a booking.
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="addons")
    addon = models.ForeignKey(Addon, on_delete=models.PROTECT, related_name="booking_addons")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.addon.name} x {self.quantity} for {self.booking.booking_number}"


class PricingRule(AuditableMixin):
    """
    Configurable dynamic pricing matrix.
    Supports flat, hourly, daily, night-based, or per-person models.
    """
    PRICING_MODELS = (
        ('FLAT', 'Flat Rate'),
        ('HOURLY', 'Per Hour'),
        ('DAILY', 'Per Day'),
        ('PER_NIGHT', 'Per Night'),
        ('PER_HEAD', 'Per Person'),
        ('PER_UNIT', 'Per Unit'),
    )
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="pricing_rules")
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE, related_name="pricing_rules")
    pricing_model = models.CharField(max_length=20, choices=PRICING_MODELS)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    peak_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    weekend_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="RuleEngine conditions in JSON. E.g. {'min_hours': 2, 'max_days': 5}"
    )
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Pricing Rule"
        verbose_name_plural = "Pricing Rules"

    def __str__(self) -> str:
        return f"{self.resource_type.name} - {self.get_pricing_model_display()} (${self.base_price})"


class TaxRule(AuditableMixin):
    """
    Tax rates/slabs linked to dynamic pricing calculation.
    """
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name="tax_rules")
    name = models.CharField(max_length=50)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Tax percentage slab (e.g. 18.00 for 18% GST).")
    is_inclusive = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tax Rule"
        verbose_name_plural = "Tax Rules"

    def __str__(self) -> str:
        type_str = "Inclusive" if self.is_inclusive else "Exclusive"
        return f"{self.name} - {self.rate}% ({type_str})"


class Review(AuditableMixin):
    """
    Customer feedback left after a Booking is marked COMPLETED.
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField(help_text="Rating on scale of 1 to 5.")
    comment = models.TextField(blank=True)

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Rating must be between 1 and 5.")
        if self.booking.status != 'Completed':
            raise ValidationError("Reviews can only be written for completed bookings.")

    def __str__(self) -> str:
        return f"Review for {self.booking.booking_number} ({self.rating}/5)"
