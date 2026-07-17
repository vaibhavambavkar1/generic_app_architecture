import datetime
import math
from decimal import Decimal
from django.db import models
from django.utils import timezone
from ..models import BusinessProfile, Resource, PricingRule, TaxRule


class PricingEngine:
    """
    Calculates dynamic pricing based on PricingRules, duration, multipliers, and taxes.
    """

    @staticmethod
    def calculate_price(
        business: BusinessProfile,
        resource: Resource,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        quantity: int = 1,
        addons: list[dict] = None
    ) -> dict:
        """
        Calculates pricing breakdown for a booking.
        addons: list of {"addon": Addon, "quantity": int}
        Returns: {
            "subtotal": Decimal,
            "tax_amount": Decimal,
            "discount_amount": Decimal,
            "total_amount": Decimal,
            "unit_price": Decimal,
            "duration_units": float,
        }
        """
        # Ensure timezone awareness
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)

        # 1. Fetch PricingRule
        # Search active rules for this Resource's type
        pricing_rule = PricingRule.objects.filter(
            business=business,
            resource_type=resource.resource_type,
            valid_from__lte=start_dt.date()
        ).filter(
            models.Q(valid_to__gte=start_dt.date()) | models.Q(valid_to__isnull=True)
        ).first()

        if not pricing_rule:
            # Return zero if no rule configured, or handle fallback
            base_price = Decimal("0.00")
            pricing_model = "FLAT"
            peak_multiplier = Decimal("1.00")
            weekend_multiplier = Decimal("1.00")
        else:
            base_price = pricing_rule.base_price
            pricing_model = pricing_rule.pricing_model
            peak_multiplier = pricing_rule.peak_multiplier
            weekend_multiplier = pricing_rule.weekend_multiplier

        # Calculate duration units
        duration = end_dt - start_dt
        duration_units = 1.0

        if pricing_model == 'HOURLY':
            duration_units = max(1.0, math.ceil(duration.total_seconds() / 3600.0))
        elif pricing_model == 'DAILY':
            duration_units = max(1.0, math.ceil(duration.total_seconds() / 86400.0))
        elif pricing_model == 'PER_NIGHT':
            # Hotel model: calculated in nights
            duration_units = max(1, duration.days)
        elif pricing_model == 'PER_HEAD':
            # Pricing based on capacity/quantity rather than time
            duration_units = float(quantity)

        # 2. Multipliers
        # Check if weekend (start_dt is Saturday/Sunday or end_dt overlaps)
        # Weekday: Monday=0, Sunday=6
        is_weekend = start_dt.weekday() in [5, 6] or end_dt.weekday() in [5, 6]
        multiplier = Decimal("1.00")
        if is_weekend:
            multiplier *= weekend_multiplier

        # Apply peak multiplier
        multiplier *= peak_multiplier

        unit_price = base_price * multiplier
        subtotal = unit_price * Decimal(str(duration_units)) * Decimal(str(quantity))

        # 3. Addons
        addon_total = Decimal("0.00")
        if addons:
            for item in addons:
                addon = item["addon"]
                addon_qty = item["quantity"]
                addon_total += addon.price * Decimal(str(addon_qty))

        subtotal += addon_total

        # 4. Tax Calculation
        # Fetch active tax rules for business
        tax_rules = TaxRule.objects.filter(business=business)
        tax_amount = Decimal("0.00")
        has_exclusive_tax = False

        for tax in tax_rules:
            tax_rate = Decimal(str(tax.rate))
            if tax.is_inclusive:
                # Tax is already in subtotal: subtotal - (subtotal / (1 + rate/100))
                tax_amount += subtotal - (subtotal / (Decimal("1.00") + (tax_rate / Decimal("100.00"))))
            else:
                # Tax added on top
                tax_amount += subtotal * (tax_rate / Decimal("100.00"))
                has_exclusive_tax = True

        discount_amount = Decimal("0.00")  # Placeholder for future dynamic promo codes

        # Total amount adds exclusive taxes
        total_amount = subtotal + (tax_amount if has_exclusive_tax else Decimal("0.00")) - discount_amount

        return {
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "tax_amount": tax_amount.quantize(Decimal("0.01")),
            "discount_amount": discount_amount.quantize(Decimal("0.01")),
            "total_amount": total_amount.quantize(Decimal("0.01")),
            "unit_price": unit_price.quantize(Decimal("0.01")),
            "duration_units": duration_units
        }
