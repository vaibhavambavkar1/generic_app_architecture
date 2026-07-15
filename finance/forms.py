from django import forms
from .models import Account, JournalEntry, JournalEntryLine

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['entry_number', 'reference', 'notes']
        widgets = {
            'entry_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
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
