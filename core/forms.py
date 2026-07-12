from django import forms
from .models import Organization

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'owner_name', 'address', 'email', 'phone', 'gstin', 'license_number', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'owner_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'address': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'gstin': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'license_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
        }
