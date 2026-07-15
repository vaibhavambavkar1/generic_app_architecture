from django import forms
from .models import Employee, LeaveRequest, ExpenseClaim

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['user', 'employee_id', 'department', 'designation', 'date_of_joining', 'manager', 'annual_leave_balance', 'sick_leave_balance']
        widgets = {
            'user': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'employee_id': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'department': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'designation': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'manager': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'annual_leave_balance': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'sick_leave_balance': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
        }

from django.contrib.auth import get_user_model
User = get_user_model()

class EmployeeCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input input-bordered w-full'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}))

    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'password', 'employee_id', 'department', 'designation', 'date_of_joining', 'manager', 'annual_leave_balance', 'sick_leave_balance']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'department': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'designation': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'manager': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'annual_leave_balance': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'sick_leave_balance': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
        }

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],  # Using email as username for simplicity
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        employee = super().save(commit=False)
        employee.user = user
        if commit:
            employee.save()
        return employee

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'employee': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'leave_type': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'start_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
        }

class ExpenseClaimForm(forms.ModelForm):
    class Meta:
        model = ExpenseClaim
        fields = ['employee', 'title', 'amount', 'receipt', 'date_incurred', 'description']
        widgets = {
            'employee': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'receipt': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
            'date_incurred': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
        }

from .models import JobPosting, Candidate

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['title', 'department', 'location', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'department': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'location': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle toggle-primary'}),
        }

class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['job', 'first_name', 'last_name', 'email', 'phone', 'resume', 'notes']
        widgets = {
            'job': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'resume': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
        }

from .models import SalaryStructure

class SalaryStructureForm(forms.ModelForm):
    class Meta:
        model = SalaryStructure
        fields = ['employee', 'base_salary', 'hra', 'other_allowances', 'tax_deductions']
        widgets = {
            'employee': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'base_salary': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'hra': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'other_allowances': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'tax_deductions': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
        }

from .models import PerformanceAppraisal, OKR

class PerformanceAppraisalForm(forms.ModelForm):
    class Meta:
        model = PerformanceAppraisal
        fields = ['employee', 'review_period', 'self_evaluation', 'manager_feedback', 'overall_rating']
        widgets = {
            'employee': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'review_period': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g., Q3 2026'}),
            'self_evaluation': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 4}),
            'manager_feedback': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 4}),
            'overall_rating': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }

class OKRForm(forms.ModelForm):
    class Meta:
        model = OKR
        fields = ['objective', 'key_result', 'completion_percentage']
        widgets = {
            'objective': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'key_result': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'completion_percentage': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 0, 'max': 100}),
        }
