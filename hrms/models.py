from django.db import models
from django.conf import settings
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition

class Employee(AuditableMixin):
    """
    Central employee profile linking to Django's built-in User.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    date_of_joining = models.DateField(blank=True, null=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # Leave Balances
    annual_leave_balance = models.IntegerField(default=20)
    sick_leave_balance = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class LeaveRequest(WorkflowMixin):
    """
    Leave request workflow.
    States: Draft -> Pending Manager -> Pending HR -> Approved / Rejected
    """
    LEAVE_TYPES = [
        ('Annual', 'Annual Leave'),
        ('Sick', 'Sick Leave'),
        ('Unpaid', 'Unpaid Leave')
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    
    @property
    def days_requested(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @transition(field='status', source='Draft', target='Pending Manager')
    def submit(self):
        pass

    @transition(field='status', source='Pending Manager', target='Pending HR')
    def manager_approve(self):
        pass

    @transition(field='status', source='Pending HR', target='Approved')
    def hr_approve(self):
        # Deduct leave balance
        if self.leave_type == 'Annual':
            self.employee.annual_leave_balance -= self.days_requested
        elif self.leave_type == 'Sick':
            self.employee.sick_leave_balance -= self.days_requested
        self.employee.save()

    @transition(field='status', source=['Pending Manager', 'Pending HR'], target='Rejected')
    def reject(self):
        pass

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.leave_type} ({self.start_date} to {self.end_date})"


class ExpenseClaim(WorkflowMixin):
    """
    Expense reimbursement workflow.
    States: Draft -> Pending Manager -> Pending Finance -> Paid / Rejected
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='expense_claims')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.ImageField(upload_to='expenses/receipts/', blank=True, null=True)
    date_incurred = models.DateField()
    description = models.TextField(blank=True)

    @transition(field='status', source='Draft', target='Pending Manager')
    def submit(self):
        pass

    @transition(field='status', source='Pending Manager', target='Pending Finance')
    def manager_approve(self):
        pass

    @transition(field='status', source='Pending Finance', target='Paid')
    def finance_pay(self):
        pass

    @transition(field='status', source=['Pending Manager', 'Pending Finance'], target='Rejected')
    def reject(self):
        pass

    def __str__(self):
        return f"{self.title} - {self.employee.user.get_full_name()} (₹{self.amount})"


class JobPosting(AuditableMixin):
    """
    Open job requisitions for the ATS module.
    """
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default='Remote')
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.department})"


class Candidate(WorkflowMixin):
    """
    Candidate pipeline for ATS.
    States: Applied -> Phone Screen -> Technical Interview -> Offer Extended -> Hired / Rejected
    """
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='candidates')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    notes = models.TextField(blank=True)

    @transition(field='status', source='Applied', target='Phone Screen')
    def schedule_phone_screen(self):
        pass

    @transition(field='status', source='Phone Screen', target='Technical Interview')
    def schedule_technical(self):
        pass

    @transition(field='status', source='Technical Interview', target='Offer Extended')
    def extend_offer(self):
        pass

    @transition(field='status', source='Offer Extended', target='Hired')
    def mark_hired(self):
        pass

    @transition(field='status', source=['Applied', 'Phone Screen', 'Technical Interview', 'Offer Extended'], target='Rejected')
    def reject(self):
        pass

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.job.title}"

from decimal import Decimal

class SalaryStructure(AuditableMixin):
    """
    Defines the compensation structure for an employee.
    """
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="House Rent Allowance")
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    @property
    def net_salary(self):
        return self.base_salary + self.hra + self.other_allowances - self.tax_deductions

    def __str__(self):
        return f"Salary Structure - {self.employee.user.get_full_name()}"

class Payslip(AuditableMixin):
    """
    Monthly generated payslip for an employee.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    month = models.DateField(help_text="The month and year for this payslip (e.g., 2026-07-01)")
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2)
    tax_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Payslip - {self.employee.user.get_full_name()} ({self.month.strftime('%B %Y')})"

class PerformanceAppraisal(WorkflowMixin):
    """
    Performance review cycle workflow.
    States: Self-Assessment -> Manager Review -> HR Approval -> Completed
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='appraisals')
    review_period = models.CharField(max_length=100, help_text="e.g., Q3 2026 or Annual 2026")
    self_evaluation = models.TextField(blank=True, help_text="Employee's self-assessment")
    manager_feedback = models.TextField(blank=True, help_text="Manager's evaluation and feedback")
    overall_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True, help_text="1 to 5 Scale")

    @transition(field='status', source='Draft', target='Self-Assessment')
    def start_self_assessment(self):
        pass

    @transition(field='status', source='Self-Assessment', target='Manager Review')
    def submit_to_manager(self):
        pass

    @transition(field='status', source='Manager Review', target='HR Approval')
    def submit_to_hr(self):
        pass

    @transition(field='status', source='HR Approval', target='Completed')
    def finalize_appraisal(self):
        pass

    def __str__(self):
        return f"Appraisal for {self.employee.user.get_full_name()} - {self.review_period}"


class OKR(AuditableMixin):
    """
    Objectives and Key Results for an employee, linked to an appraisal cycle.
    """
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='okrs')
    objective = models.CharField(max_length=255)
    key_result = models.TextField()
    completion_percentage = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.objective} ({self.completion_percentage}%)"
