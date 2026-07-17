from django import forms
from .models import PurchaseRequest, GoodsReceiptNote, StorePurchaseOrder, PurchaseRequestItem, GRNLineItem

class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['department', 'expected_date', 'notes']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'expected_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
        }

class PurchaseRequestItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestItem
        fields = ['product', 'quantity', 'description']
        widgets = {
            'product': forms.Select(attrs={'class': 'select select-bordered w-full select-sm'}),
            'quantity': forms.NumberInput(attrs={'class': 'input input-bordered w-full input-sm', 'min': 1}),
            'description': forms.TextInput(attrs={'class': 'input input-bordered w-full input-sm'}),
        }

class GRNForm(forms.ModelForm):
    class Meta:
        model = GoodsReceiptNote
        fields = ['purchase_order', 'supplier_challan_number']
        widgets = {
            'purchase_order': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'supplier_challan_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['purchase_order'].queryset = StorePurchaseOrder.objects.filter(
            status__in=['Issued', 'Partially Received']
        )

class GRNLineItemForm(forms.ModelForm):
    class Meta:
        model = GRNLineItem
        fields = ['product', 'po_line', 'expected_quantity', 'received_quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'select select-bordered w-full select-sm'}),
            'po_line': forms.Select(attrs={'class': 'select select-bordered w-full select-sm'}),
            'expected_quantity': forms.NumberInput(attrs={'class': 'input input-bordered w-full input-sm', 'readonly': True}),
            'received_quantity': forms.NumberInput(attrs={'class': 'input input-bordered w-full input-sm', 'min': 0}),
        }
