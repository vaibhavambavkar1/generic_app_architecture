from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition
from generic_store_mgmt.models import Product
from crm.models import Customer
from inventory.models import Warehouse, StockLedger

class Quotation(WorkflowMixin):
    """
    Price quote sent to a customer.
    Draft -> Sent -> Accepted -> Rejected
    """
    quote_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='quotations')
    valid_until = models.DateField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    @transition(field='status', source='Draft', target='Sent')
    def send_quote(self):
        pass

    @transition(field='status', source='Sent', target='Accepted')
    def accept_quote(self):
        pass

class QuotationLineItem(AuditableMixin):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

class SalesOrder(WorkflowMixin):
    """
    Confirmed order from customer.
    Draft -> Confirmed -> Shipped -> Delivered
    """
    so_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders')
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    expected_dispatch_date = models.DateField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    @transition(field='status', source='Draft', target='Confirmed')
    def confirm_order(self):
        pass

    @transition(field='status', source='Confirmed', target='Shipped')
    def ship_order(self):
        # In a full ERP, this would trigger Delivery Challan and Stock Out
        pass

class POSInvoice(AuditableMixin):
    """
    Direct POS billing for walk-in customers or over the counter sales.
    These bypass the complex SO workflow and immediately update stock.
    """
    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('UPI', 'UPI'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='CASH')
    is_paid = models.BooleanField(default=False)

    def process_payment(self):
        self.is_paid = True
        self.save()
        # Create stock ledger entries for each line item (Stock OUT)
        for line in self.lines.all():
            StockLedger.objects.create(
                product=line.product,
                warehouse=self.warehouse,
                transaction_type='SALES',
                quantity=-line.quantity, # Negative for outgoing
                reference_document=self.invoice_number
            )
            
        # Automate Journal Entry for Finance Ledger
        from finance.models import JournalEntry, JournalEntryLine, Account
        
        # Look for default accounts
        cash_account = Account.objects.filter(code='1000').first() # E.g., Cash Asset
        revenue_account = Account.objects.filter(code='4000').first() # E.g., Sales Revenue
        
        if cash_account and revenue_account:
            je = JournalEntry.objects.create(
                entry_number=f"JE-POS-{self.invoice_number}",
                reference=self.invoice_number,
                notes=f"POS Sale - {self.get_payment_method_display()}",
                is_posted=True # Automatically post it
            )
            # Debit Cash
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=cash_account,
                debit=self.total_amount,
                description=f"Received payment for {self.invoice_number}"
            )
            # Credit Revenue
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=revenue_account,
                credit=self.total_amount,
                description=f"Sales revenue from {self.invoice_number}"
            )

class POSLineItem(AuditableMixin):
    invoice = models.ForeignKey(POSInvoice, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
