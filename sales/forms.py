from django import forms
from .models import Quotation, SalesOrder, POSInvoice, QuotationLineItem

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['quote_number', 'customer', 'valid_until']
        widgets = {
            'quote_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'customer': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'valid_until': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
        }

class QuotationLineItemForm(forms.ModelForm):
    class Meta:
        model = QuotationLineItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'select select-bordered w-full select-sm'}),
            'quantity': forms.NumberInput(attrs={'class': 'input input-bordered w-full input-sm', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'input input-bordered w-full input-sm', 'step': '0.01'}),
        }

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['so_number', 'customer', 'quotation', 'warehouse', 'expected_dispatch_date']
        widgets = {
            'so_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'customer': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'quotation': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'warehouse': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'expected_dispatch_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
        }
