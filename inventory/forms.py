from django import forms
from .models import InventoryItem, Supplier, PurchaseOrder, POLineItem

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['sku', 'name', 'description', 'stock_level', 'reorder_threshold', 'unit_price', 'has_expiry_date']
        widgets = {
            'sku': forms.TextInput(attrs={'placeholder': 'Auto-generated if left blank'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'has_expiry_date' in self.fields:
            self.fields['has_expiry_date'].widget.template_name = 'inventory/widgets/checkbox.html'
        if self.instance and self.instance.pk:
            self.fields['stock_level'].disabled = True
            self.fields['stock_level'].required = False
            self.fields['stock_level'].widget.attrs.update({
                'class': 'bg-base-300 cursor-not-allowed font-medium text-base-content/50'
            })

class SupplierCatalogProductForm(forms.ModelForm):
    supplier_price = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label="Supplier Price")

    class Meta:
        model = InventoryItem
        fields = ['sku', 'name', 'description', 'stock_level', 'reorder_threshold', 'unit_price', 'has_expiry_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered textarea-sm w-full'}),
            'sku': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full font-mono', 'placeholder': 'Auto-generated if left blank'}),
            'name': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'stock_level': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'reorder_threshold': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'unit_price': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full font-mono'}),
            'has_expiry_date': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary checkbox-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'has_expiry_date' in self.fields:
            self.fields['has_expiry_date'].widget.template_name = 'inventory/widgets/checkbox.html'

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_email', 'phone', 'address', 'gst_number']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['po_number', 'supplier']

from .models import StockAdjustment

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = ['warehouse', 'product', 'quantity_adjusted', 'reason']
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'product': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'quantity_adjusted': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'placeholder': '+5 or -2'}),
            'reason': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g., Audit match, Expiry, Damage'}),
        }
