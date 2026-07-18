from django.db.models.signals import post_save
from django.dispatch import receiver
from courier.models import Waybill
from freight.models import FreightBooking
from wms_3pl.models import PutawayTask
from finance.models import JournalEntry, JournalEntryLine, Account

@receiver(post_save, sender=Waybill)
def generate_waybill_invoice(sender, instance, **kwargs):
    if instance.status == 'Delivered' and instance.price > 0:
        if not JournalEntry.objects.filter(reference=instance.waybill_number).exists():
            ar_account = Account.objects.filter(code='1100').first() # AR
            revenue_account = Account.objects.filter(code='4000').first() # Revenue
            
            if ar_account and revenue_account:
                je = JournalEntry.objects.create(
                    entry_number=f"JE-WAYBILL-{instance.waybill_number}",
                    reference=instance.waybill_number,
                    notes=f"Revenue for Delivered Waybill {instance.waybill_number}",
                    is_posted=True
                )
                JournalEntryLine.objects.create(
                    journal_entry=je, account=ar_account, debit=instance.price, 
                    description="AR for Waybill", customer=instance.sender
                )
                JournalEntryLine.objects.create(
                    journal_entry=je, account=revenue_account, credit=instance.price, 
                    description="Waybill Revenue"
                )

@receiver(post_save, sender=FreightBooking)
def generate_freight_financials(sender, instance, **kwargs):
    if instance.status == 'Delivered':
        # In a real scenario, price would be calculated dynamically. For Phase 5 demonstration, we use a fixed revenue logic.
        freight_revenue = 1500.00
        
        if not JournalEntry.objects.filter(reference=instance.booking_number).exists():
            ar_account = Account.objects.filter(code='1100').first()
            revenue_account = Account.objects.filter(code='4000').first()
            ap_account = Account.objects.filter(code='2000').first()
            expense_account = Account.objects.filter(code='5000').first()
            
            # AR Generation
            if ar_account and revenue_account:
                je_ar = JournalEntry.objects.create(
                    entry_number=f"JE-FRT-AR-{instance.booking_number}",
                    reference=instance.booking_number,
                    notes=f"Revenue for Freight {instance.booking_number}",
                    is_posted=True
                )
                JournalEntryLine.objects.create(
                    journal_entry=je_ar, account=ar_account, debit=freight_revenue, 
                    description="AR for Freight", customer=instance.shipper
                )
                JournalEntryLine.objects.create(
                    journal_entry=je_ar, account=revenue_account, credit=freight_revenue, 
                    description="Freight Revenue"
                )
            
            # AP Generation for Carrier Legs
            if ap_account and expense_account:
                for leg in instance.legs.all():
                    if leg.carrier:
                        carrier_cost = 400.00 # Placeholder for carrier cost
                        je_ap = JournalEntry.objects.create(
                            entry_number=f"JE-FRT-AP-{leg.id}",
                            reference=f"{instance.booking_number}-LEG-{leg.sequence}",
                            notes=f"Carrier Cost for Leg {leg.sequence}",
                            is_posted=True
                        )
                        JournalEntryLine.objects.create(
                            journal_entry=je_ap, account=expense_account, debit=carrier_cost, 
                            description=f"Freight Expense Leg {leg.sequence}"
                        )
                        JournalEntryLine.objects.create(
                            journal_entry=je_ap, account=ap_account, credit=carrier_cost, 
                            description=f"AP to Carrier", supplier=leg.carrier
                        )

@receiver(post_save, sender=PutawayTask)
def bill_wms_storage(sender, instance, **kwargs):
    """ Bill 3PL clients automatically when goods are put away (receiving/handling fee). """
    if instance.status == 'Completed':
        if not JournalEntry.objects.filter(reference=instance.task_number).exists():
            ar_account = Account.objects.filter(code='1100').first()
            revenue_account = Account.objects.filter(code='4000').first()
            handling_fee = instance.quantity * 2.50 # Example: $2.50 per unit handling fee
            
            if ar_account and revenue_account and handling_fee > 0:
                je = JournalEntry.objects.create(
                    entry_number=f"JE-WMS-{instance.task_number}",
                    reference=instance.task_number,
                    notes=f"3PL Handling Fee for Putaway {instance.task_number}",
                    is_posted=True
                )
                JournalEntryLine.objects.create(
                    journal_entry=je, account=ar_account, debit=handling_fee, 
                    description="AR for 3PL Handling", customer=instance.client
                )
                JournalEntryLine.objects.create(
                    journal_entry=je, account=revenue_account, credit=handling_fee, 
                    description="3PL Service Revenue"
                )
