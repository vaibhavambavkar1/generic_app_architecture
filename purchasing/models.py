from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition
from generic_store_mgmt.models import Product
from inventory.models import Supplier, Warehouse, StockLedger
from django.contrib.contenttypes.fields import GenericRelation

class PurchaseRequest(WorkflowMixin):
    """
    Internal request for goods.
    Draft -> Submitted -> Approved -> Rejected
    """
    request_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    expected_date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"PR: {self.request_number} - {self.status}"

    @transition(field='status', source='Draft', target='Submitted')
    def submit_pr(self):
        pass

    @transition(field='status', source='Submitted', target='Approved')
    def approve_pr(self):
        pass

    @transition(field='status', source='Submitted', target='Rejected')
    def reject_pr(self):
        pass

    def save(self, *args, **kwargs):
        if not self.request_number:
            import uuid
            self.request_number = f"PR-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class PurchaseRequestItem(AuditableMixin):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    description = models.CharField(max_length=255, blank=True)

class RequestForQuotation(WorkflowMixin):
    """
    RFQ sent to multiple suppliers.
    Draft -> Sent -> Closed
    """
    rfq_number = models.CharField(max_length=50, unique=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True)
    suppliers = models.ManyToManyField(Supplier, related_name='rfqs')
    deadline = models.DateField()

    @transition(field='status', source='Draft', target='Sent')
    def send_rfq(self):
        pass

    def save(self, *args, **kwargs):
        if not self.rfq_number:
            import uuid
            self.rfq_number = f"RFQ-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"RFQ: {self.rfq_number}"

class StorePurchaseOrder(WorkflowMixin):
    """
    Purchase Order issued to a single supplier.
    Draft -> Issued -> Partially Received -> Fully Received
    """
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    expected_delivery = models.DateField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    payments = GenericRelation('core.PaymentTransaction')

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

    @transition(field='status', source='Draft', target='Issued')
    def issue_po(self):
        pass

    @transition(field='status', source=['Issued', 'Partially Received'], target='Partially Received')
    def partially_receive(self):
        pass

    @transition(field='status', source=['Issued', 'Partially Received'], target='Fully Received')
    def fully_receive(self):
        pass

    def save(self, *args, **kwargs):
        if not self.po_number:
            import uuid
            self.po_number = f"PO-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class StorePOLineItem(AuditableMixin):
    po = models.ForeignKey(StorePurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price

class GoodsReceiptNote(WorkflowMixin):
    """
    GRN records the physical receipt of goods.
    Draft -> Received (Triggers StockLedger insertion)
    """
    grn_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(StorePurchaseOrder, on_delete=models.PROTECT, related_name='grns')
    received_date = models.DateField(auto_now_add=True)
    supplier_challan_number = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"GRN: {self.grn_number}"
    
    @transition(field='status', source='Draft', target='Received')
    def receive_goods(self):
        # Update PO Status based on fulfillment logic (simplified here)
        total_received_value = 0
        for line in self.lines.all():
            # Update Stock
            StockLedger.objects.create(
                product=line.product,
                warehouse=self.purchase_order.warehouse,
                transaction_type='PURCHASE',
                quantity=line.received_quantity,
                reference_document=self.grn_number
            )
            # Calculate value (using PO price if available)
            if line.po_line:
                total_received_value += (line.received_quantity * line.po_line.unit_price)
        
        # We can transition the PO as well
        if self.purchase_order.status != 'Fully Received':
            self.purchase_order.partially_receive()
            self.purchase_order.save()
            
        # Automate Journal Entry for Finance Ledger (Inventory Asset & AP)
        if total_received_value > 0:
            from finance.models import JournalEntry, JournalEntryLine, Account
            
            # Lookup default accounts
            inventory_account = Account.objects.filter(code='1200').first() # E.g., Inventory Asset
            ap_account = Account.objects.filter(code='2000').first() # E.g., Accounts Payable
            
            if inventory_account and ap_account:
                je = JournalEntry.objects.create(
                    entry_number=f"JE-GRN-{self.grn_number}",
                    reference=self.grn_number,
                    notes=f"Goods Receipt Note from PO: {self.purchase_order.po_number}",
                    is_posted=True
                )
                # Debit Inventory (Asset increases)
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=inventory_account,
                    debit=total_received_value,
                    description=f"Inventory received on {self.grn_number}"
                )
                # Credit Accounts Payable (Liability increases)
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=ap_account,
                    credit=total_received_value,
                    description=f"Payable to {self.purchase_order.supplier.name}",
                    supplier=self.purchase_order.supplier
                )

    def save(self, *args, **kwargs):
        if not self.grn_number:
            import uuid
            self.grn_number = f"GRN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class GRNLineItem(AuditableMixin):
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='lines')
    po_line = models.ForeignKey(StorePOLineItem, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    expected_quantity = models.PositiveIntegerField()
    received_quantity = models.PositiveIntegerField()

class SupplierBill(WorkflowMixin):
    """
    Formal Supplier Bill (AP) generated against Purchase Orders and GRNs.
    """
    bill_number = models.CharField(max_length=50, unique=True)
    supplier_invoice_reference = models.CharField(max_length=100, blank=True)
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.PROTECT, related_name='bills')
    purchase_order = models.ForeignKey(StorePurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.SET_NULL, null=True, blank=True)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.bill_number} - {self.supplier}"

    @transition(field='status', source='Draft', target='Verified')
    def verify_bill(self):
        # Generate Journal Entries
        from finance.models import JournalEntry, JournalEntryLine, Account
        
        ap_account = Account.objects.filter(code='2000').first()
        grn_clearing = Account.objects.filter(code='2010').first()
        expense_account = Account.objects.filter(code='5000').first() # COGS or generic expense
        tax_account = Account.objects.filter(code='2100').first() # Tax payable/receivable
        
        # If GRN clearing doesn't exist but we need it, we can fallback to Expense for simplicity,
        # or ideally create it. Let's get or create GRN Clearing
        if not grn_clearing and ap_account:
            # We'll just fallback to expense if 2010 is completely missing to avoid crash
            debit_account = expense_account
        else:
            debit_account = grn_clearing if self.grn else expense_account
            
        if ap_account and debit_account:
            je = JournalEntry.objects.create(
                entry_number=f"JE-BILL-{self.bill_number}",
                reference=self.bill_number,
                notes=f"Supplier Bill Verification - {self.supplier.name}",
                is_posted=True
            )
            # Credit AP (Liability increases)
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=ap_account,
                credit=self.total_amount,
                description=f"Payable to {self.supplier.name} for {self.bill_number}",
                supplier=self.supplier
            )
            # Debit GRN Clearing or Expense
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=debit_account,
                debit=self.subtotal,
                description=f"Expense/Clearing for {self.bill_number}"
            )
            if self.tax_amount > 0 and tax_account:
                # Assuming tax on purchases is a debit (input tax credit)
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=tax_account,
                    debit=self.tax_amount,
                    description=f"Tax input for {self.bill_number}"
                )

    def save(self, *args, **kwargs):
        if not self.bill_number:
            import uuid
            self.bill_number = f"BILL-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class SupplierBillLine(AuditableMixin):
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
