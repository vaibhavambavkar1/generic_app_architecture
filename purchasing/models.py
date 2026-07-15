from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition
from generic_store_mgmt.models import Product
from inventory.models import Supplier, Warehouse, StockLedger

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

    @transition(field='status', source='Draft', target='Issued')
    def issue_po(self):
        pass

    @transition(field='status', source=['Issued', 'Partially Received'], target='Partially Received')
    def partially_receive(self):
        pass

    @transition(field='status', source=['Issued', 'Partially Received'], target='Fully Received')
    def fully_receive(self):
        pass

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

class GRNLineItem(AuditableMixin):
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='lines')
    po_line = models.ForeignKey(StorePOLineItem, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    expected_quantity = models.PositiveIntegerField()
    received_quantity = models.PositiveIntegerField()
