from django import forms
from .models import InventoryItem, Supplier, PurchaseOrder, POLineItem

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['sku', 'name', 'description', 'stock_level', 'reorder_threshold', 'unit_price', 'has_expiry_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SupplierCatalogProductForm(forms.ModelForm):
    supplier_price = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label="Supplier Price")

    class Meta:
        model = InventoryItem
        fields = ['sku', 'name', 'description', 'stock_level', 'reorder_threshold', 'unit_price', 'has_expiry_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered textarea-sm w-full'}),
            'sku': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full font-mono'}),
            'name': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'stock_level': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'reorder_threshold': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full'}),
            'unit_price': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full font-mono'}),
            'has_expiry_date': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary checkbox-sm'}),
        }

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
