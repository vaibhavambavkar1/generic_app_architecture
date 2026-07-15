from django import forms
from .models import Customer, Lead

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address', 'industry', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'address': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'industry': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['title', 'customer', 'value', 'expected_close_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'customer': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'value': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
        }
