from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'barcode', 'product_type', 'category', 'brand', 'uom', 'tax_bracket', 'purchase_price', 'selling_price', 'mrp', 'manage_stock', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'sku': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'barcode': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'product_type': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'category': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'brand': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'uom': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'tax_bracket': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'selling_price': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'mrp': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'manage_stock': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }
