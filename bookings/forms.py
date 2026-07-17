from django import forms
from .models import BusinessProfile, Resource, OperatingSchedule

class BusinessSetupForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = ['name', 'industry', 'timezone', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'industry': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'timezone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'currency': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'code', 'resource_type', 'capacity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'code': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'resource_type': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'capacity': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle toggle-primary'}),
        }

class OperatingScheduleForm(forms.ModelForm):
    class Meta:
        model = OperatingSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'slot_duration_minutes', 'max_concurrent', 'resource', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'start_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full', 'type': 'time'}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'max_concurrent': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'resource': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle toggle-primary'}),
        }
