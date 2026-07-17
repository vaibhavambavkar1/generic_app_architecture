from django import forms
from .models import Account, JournalEntry, JournalEntryLine

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'category', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'category': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['reference', 'notes']
        widgets = {
            'reference': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
        }

class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'debit', 'credit', 'description']
        widgets = {
            'account': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'debit': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'step': '0.01'}),
            'credit': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'input input-bordered input-sm w-full'}),
        }
