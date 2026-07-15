from django import forms
from .models import Asset, AssetCategory, MaintenanceRecord

class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full'}),
        }

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'category', 'serial_number', 'barcode', 'purchase_date', 'purchase_cost', 'warranty_expiry']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'category': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'serial_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'barcode': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Leave blank to auto-generate'}),
            'purchase_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': '0.01'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
        }

class MaintenanceRecordForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ['date', 'cost', 'description', 'performed_by']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'cost': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full'}),
            'performed_by': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }
