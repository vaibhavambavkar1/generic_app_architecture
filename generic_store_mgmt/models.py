from django.db import models
from core.mixins import AuditableMixin
from django.utils.translation import gettext_lazy as _

class Category(AuditableMixin):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

class Brand(AuditableMixin):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class UnitOfMeasure(AuditableMixin):
    name = models.CharField(max_length=50, help_text="e.g., Kilogram, Piece, Box")
    code = models.CharField(max_length=10, unique=True, help_text="e.g., KG, PCS, BOX")

    class Meta:
        verbose_name_plural = "Units of Measure"

    def __str__(self):
        return f"{self.name} ({self.code})"

class TaxBracket(AuditableMixin):
    name = models.CharField(max_length=50, help_text="e.g., GST 18%")
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Central GST %")
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="State GST %")
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Integrated GST %")
    is_active = models.BooleanField(default=True)

    @property
    def total_rate(self):
        return self.cgst_rate + self.sgst_rate

    def __str__(self):
        return f"{self.name} ({self.total_rate}%)"

class Product(AuditableMixin):
    PRODUCT_TYPES = (
        ('goods', 'Goods'),
        ('service', 'Service'),
    )
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, blank=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES, default='goods')
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='products')
    tax_bracket = models.ForeignKey(TaxBracket, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    mrp = models.DecimalField("Maximum Retail Price", max_digits=12, decimal_places=2, null=True, blank=True)

    # Inventory Policies
    manage_stock = models.BooleanField(default=True, help_text="Track inventory for this product?")
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.sku:
            import uuid
            self.sku = f"PROD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} [{self.sku}]"

class PriceList(AuditableMixin):
    """Multiple price lists (e.g. Retail, Wholesale)"""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PriceListItem(AuditableMixin):
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_list_items')
    rate = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('price_list', 'product')

    def __str__(self):
        return f"{self.product.name} @ {self.rate} in {self.price_list.name}"
