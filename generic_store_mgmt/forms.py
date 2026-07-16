from django import forms
from .models import Product

class NormalCheckboxInput(forms.CheckboxInput):
    template_name = 'django/forms/widgets/input.html'

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
            'manage_stock': NormalCheckboxInput(attrs={'class': 'checkbox checkbox-primary checkbox-sm'}),
            'is_active': NormalCheckboxInput(attrs={'class': 'checkbox checkbox-primary checkbox-sm'}),
        }

from .models import Category, Brand, UnitOfMeasure

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'is_active': NormalCheckboxInput(attrs={'class': 'checkbox checkbox-primary checkbox-sm'}),
        }

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'is_active': NormalCheckboxInput(attrs={'class': 'checkbox checkbox-primary checkbox-sm'}),
        }

class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'code': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }
