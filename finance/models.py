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
