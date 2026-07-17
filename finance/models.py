from django.db import models
from django.core.exceptions import ValidationError
from core.mixins import AuditableMixin
from inventory.models import Supplier
from crm.models import Customer
from django.db.models import Sum

class AccountCategory(models.TextChoices):
    ASSET = 'ASSET', 'Asset'
    LIABILITY = 'LIABILITY', 'Liability'
    EQUITY = 'EQUITY', 'Equity'
    REVENUE = 'REVENUE', 'Revenue'
    EXPENSE = 'EXPENSE', 'Expense'

class Account(AuditableMixin):
    """
    Chart of Accounts (CoA)
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=AccountCategory.choices)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.category})"
        
    def save(self, *args, **kwargs):
        if not self.code:
            import uuid
            self.code = f"ACC-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
        
    @property
    def balance(self):
        """
        Calculate balance based on normal accounting rules.
        Assets/Expenses increase with Debits.
        Liabilities/Equity/Revenue increase with Credits.
        """
        debits = self.journal_lines.aggregate(Sum('debit'))['debit__sum'] or 0
        credits = self.journal_lines.aggregate(Sum('credit'))['credit__sum'] or 0
        
        if self.category in [AccountCategory.ASSET, AccountCategory.EXPENSE]:
            return debits - credits
        else:
            return credits - debits

class JournalEntry(AuditableMixin):
    """
    Double-entry accounting journal.
    """
    entry_number = models.CharField(max_length=50, unique=True)
    date = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True, help_text="e.g., PO Number, Invoice Number, GRN")
    notes = models.TextField(blank=True)
    is_posted = models.BooleanField(default=False)

    def __str__(self):
        return f"JE: {self.entry_number} on {self.date}"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            import uuid
            self.entry_number = f"JE-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def clean(self):
        """Ensure Debits = Credits before posting"""
        if self.is_posted:
            total_debits = sum(line.debit for line in self.lines.all())
            total_credits = sum(line.credit for line in self.lines.all())
            if total_debits != total_credits:
                raise ValidationError("Total Debits must equal Total Credits to post this Journal Entry.")

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    description = models.CharField(max_length=255, blank=True)
    
    # Optional links for Sub-ledger reporting
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("A line cannot have both a debit and a credit.")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("A line must have either a debit or a credit.")

class InvoicePaymentAllocation(models.Model):
    """
    Links a PaymentTransaction to specific AR/AP Invoices to handle partial and combined payments.
    """
    payment = models.ForeignKey('core.PaymentTransaction', on_delete=models.PROTECT)
    sales_invoice = models.ForeignKey('sales.B2BSalesInvoice', on_delete=models.CASCADE, null=True, blank=True, related_name='allocations')
    supplier_bill = models.ForeignKey('purchasing.SupplierBill', on_delete=models.CASCADE, null=True, blank=True, related_name='allocations')
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            from finance.models import JournalEntry, JournalEntryLine, Account
            cash_account = Account.objects.filter(code='1000').first()
            ar_account = Account.objects.filter(code='1100').first()
            ap_account = Account.objects.filter(code='2000').first()

            if self.sales_invoice:
                self.sales_invoice.amount_paid += self.allocated_amount
                self.sales_invoice.save()
                
                # Payment received from customer: Debit Cash, Credit AR
                if cash_account and ar_account:
                    je = JournalEntry.objects.create(
                        entry_number=f"JE-PAY-AR-{self.pk}",
                        reference=self.sales_invoice.invoice_number,
                        notes=f"Payment received for {self.sales_invoice.invoice_number}",
                        is_posted=True
                    )
                    JournalEntryLine.objects.create(
                        journal_entry=je, account=cash_account,
                        debit=self.allocated_amount, description="Cash received"
                    )
                    JournalEntryLine.objects.create(
                        journal_entry=je, account=ar_account,
                        credit=self.allocated_amount, description="AR reduced",
                        customer=self.sales_invoice.customer
                    )
                
            if self.supplier_bill:
                self.supplier_bill.amount_paid += self.allocated_amount
                self.supplier_bill.save()
                
                # Payment made to supplier: Debit AP, Credit Cash
                if cash_account and ap_account:
                    je = JournalEntry.objects.create(
                        entry_number=f"JE-PAY-AP-{self.pk}",
                        reference=self.supplier_bill.bill_number,
                        notes=f"Payment sent for {self.supplier_bill.bill_number}",
                        is_posted=True
                    )
                    JournalEntryLine.objects.create(
                        journal_entry=je, account=ap_account,
                        debit=self.allocated_amount, description="AP reduced",
                        supplier=self.supplier_bill.supplier
                    )
                    JournalEntryLine.objects.create(
                        journal_entry=je, account=cash_account,
                        credit=self.allocated_amount, description="Cash paid"
                    )
