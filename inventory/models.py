from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin

class Supplier(AuditableMixin):
    name = models.CharField(max_length=150, unique=True)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    supplied_items = models.ManyToManyField('InventoryItem', through='SupplierCatalogItem', related_name='suppliers', blank=True)

    def __str__(self):
        return self.name

class InventoryItem(AuditableMixin):
    sku = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    stock_level = models.IntegerField(default=0)
    reorder_threshold = models.IntegerField(default=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    barcode = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    has_expiry_date = models.BooleanField(default=False)

    def generate_barcode(self):
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO
        from django.core.files import File

        COD = barcode.get_barcode_class('code128')
        code = COD(self.sku, writer=ImageWriter())
        buffer = BytesIO()
        code.write(buffer)
        filename = f"bc_{self.sku}.png"
        
        if self.barcode:
            try:
                self.barcode.delete(save=False)
            except Exception:
                pass
            
        self.barcode.save(filename, File(buffer), save=False)

    def generate_qrcode(self):
        import qrcode
        from io import BytesIO
        from django.core.files import File

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.sku)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f"qr_{self.sku}.png"
        
        if self.qr_code:
            try:
                self.qr_code.delete(save=False)
            except Exception:
                pass
            
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if not self.sku:
            import uuid
            while True:
                candidate = f"SKU-{uuid.uuid4().hex[:8].upper()}"
                if not InventoryItem.objects.filter(sku=candidate).exists():
                    self.sku = candidate
                    break

        sku_changed = False
        old_price = None
        
        if not is_new:
            try:
                old_instance = InventoryItem.objects.only('sku', 'unit_price').get(pk=self.pk)
                old_sku = old_instance.sku
                old_price = old_instance.unit_price
                if old_sku != self.sku:
                    sku_changed = True
            except InventoryItem.DoesNotExist:
                pass
        
        if is_new or sku_changed or not self.barcode or not self.qr_code:
            self.generate_barcode()
            self.generate_qrcode()
                
        super().save(*args, **kwargs)

        if is_new or old_price != self.unit_price:
            InventoryItemPriceLog.objects.create(
                item=self,
                price=self.unit_price
            )

    def __str__(self):
        return f"{self.name} ({self.sku})"

class SupplierCatalogItem(AuditableMixin):
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='catalog_entries')
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='catalog_items')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('supplier', 'item')

    def __str__(self):
        return f"{self.supplier.name} - {self.item.name} (Rs. {self.price})"

class PurchaseOrder(WorkflowMixin):
    po_number = models.CharField(max_length=50, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.po_number:
            import datetime
            today_str = datetime.date.today().strftime('%Y%m%d')
            prefix = f"PO-{today_str}-"
            
            # Get the last sequence number for today
            latest_po = PurchaseOrder.objects.filter(po_number__startswith=prefix).order_by('-po_number').first()
            if latest_po:
                try:
                    last_sequence = int(latest_po.po_number.split('-')[-1])
                    next_sequence = last_sequence + 1
                except (ValueError, IndexError):
                    next_sequence = 1
            else:
                next_sequence = 1
                
            self.po_number = f"{prefix}{next_sequence:04d}"
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

class POLineItem(AuditableMixin):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.IntegerField(null=True, blank=True)
    received_unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def received_subtotal(self):
        qty = self.received_quantity if self.received_quantity is not None else self.quantity
        price = self.received_unit_price if self.received_unit_price is not None else self.unit_price
        return qty * price

    def __str__(self):
        return f"{self.item.name} x {self.quantity} in {self.purchase_order.po_number}"

class InventoryItemPriceLog(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='price_logs')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.item.sku} - {self.price} at {self.changed_at}"
