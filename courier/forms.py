from django import forms
from .models import DispatchManifest

class DispatchManifestForm(forms.ModelForm):
    class Meta:
        model = DispatchManifest
        fields = ['driver', 'vehicle', 'route']
        widgets = {
            'driver': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'vehicle': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'route': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }
