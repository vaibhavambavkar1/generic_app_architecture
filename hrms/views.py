from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Employee, LeaveRequest, ExpenseClaim
from .forms import EmployeeForm, EmployeeCreateForm, LeaveRequestForm, ExpenseClaimForm
from core.models import Workflow, State

@login_required
def dashboard(request):
    """HRMS Overview Dashboard."""
    total_employees = Employee.objects.count()
    pending_leaves = LeaveRequest.objects.filter(status__in=['Draft', 'Pending Manager', 'Pending HR']).count()
    pending_expenses = ExpenseClaim.objects.filter(status__in=['Draft', 'Pending Manager', 'Pending Finance']).count()
    
    return render(request, 'hrms/dashboard.html', {
        'total_employees': total_employees,
        'pending_leaves': pending_leaves,
        'pending_expenses': pending_expenses,
    })

# --- Employee Views ---

@login_required
def employee_list(request):
    employees = Employee.objects.select_related('user', 'manager').all()
    return render(request, 'hrms/employee_list.html', {'employees': employees})

@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hrms:employee_list')
    else:
        form = EmployeeCreateForm()
    return render(request, 'hrms/employee_form.html', {'form': form, 'title': 'Add Employee'})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('hrms:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'hrms/employee_form.html', {'form': form, 'title': 'Edit Employee'})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'hrms/employee_detail.html', {'employee': employee})

# --- Leave Request Views ---

@login_required
def leave_list(request):
    leaves = LeaveRequest.objects.select_related('employee__user').all()
    return render(request, 'hrms/leave_list.html', {'leaves': leaves})

@login_required
def leave_create(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            
            # Workflow integration
            workflow, _ = Workflow.objects.get_or_create(
                name='Leave Workflow', 
                defaults={'model_name': leave.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(
                name='Draft', 
                workflow=workflow,
                defaults={'is_initial': True}
            )
            leave.workflow_state = state
            leave.status = 'Draft'
            leave.save()
            return redirect('hrms:leave_list')
    else:
        form = LeaveRequestForm()
    return render(request, 'hrms/leave_form.html', {'form': form, 'title': 'Request Leave'})

@login_required
def leave_detail(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    # Extract FSM target states
    fsm_map = leave.__class__._get_fsm_transition_map()
    available_transitions = []
    
    for (source, target), method_name in fsm_map.items():
        if source == leave.status or source == '*':
            available_transitions.append({
                'name': method_name.replace('_', ' ').title(),
                'target': target,
                'method': method_name
            })
            
    if request.method == 'POST':
        method_name = request.POST.get('method')
        if method_name:
            method = getattr(leave, method_name)
            method()
            leave.save(update_fields=['status'])
            
            workflow, _ = Workflow.objects.get_or_create(
                name='Leave Workflow', 
                defaults={'model_name': leave.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(name=leave.status, workflow=workflow)
            leave.workflow_state = state
            leave.save(update_fields=['workflow_state'])
            
            return redirect('hrms:leave_detail', pk=leave.pk)
            
    return render(request, 'hrms/leave_detail.html', {'leave': leave, 'available_transitions': available_transitions})

# --- Expense Claim Views ---

@login_required
def expense_list(request):
    expenses = ExpenseClaim.objects.select_related('employee__user').all()
    return render(request, 'hrms/expense_list.html', {'expenses': expenses})

@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseClaimForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            
            # Workflow integration
            workflow, _ = Workflow.objects.get_or_create(
                name='Expense Workflow', 
                defaults={'model_name': expense.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(
                name='Draft', 
                workflow=workflow,
                defaults={'is_initial': True}
            )
            expense.workflow_state = state
            expense.status = 'Draft'
            expense.save()
            return redirect('hrms:expense_list')
    else:
        form = ExpenseClaimForm()
    return render(request, 'hrms/expense_form.html', {'form': form, 'title': 'Submit Expense Claim'})

@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(ExpenseClaim, pk=pk)
    
    # Extract FSM target states
    fsm_map = expense.__class__._get_fsm_transition_map()
    available_transitions = []
    
    for (source, target), method_name in fsm_map.items():
        if source == expense.status or source == '*':
            available_transitions.append({
                'name': method_name.replace('_', ' ').title(),
                'target': target,
                'method': method_name
            })
            
    if request.method == 'POST':
        method_name = request.POST.get('method')
        if method_name:
            method = getattr(expense, method_name)
            method()
            expense.save(update_fields=['status'])
            
            workflow, _ = Workflow.objects.get_or_create(
                name='Expense Workflow', 
                defaults={'model_name': expense.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(name=expense.status, workflow=workflow)
            expense.workflow_state = state
            expense.save(update_fields=['workflow_state'])
            
            return redirect('hrms:expense_detail', pk=expense.pk)
            
    return render(request, 'hrms/expense_detail.html', {'expense': expense, 'available_transitions': available_transitions})

# --- ATS Views ---

@login_required
def ats_dashboard(request):
    # Kanban board data
    board_columns = ['Applied', 'Phone Screen', 'Technical Interview', 'Offer Extended', 'Hired', 'Rejected']
    kanban_data = {}
    for col in board_columns:
        kanban_data[col] = Candidate.objects.filter(status=col).select_related('job')
        
    return render(request, 'hrms/ats_dashboard.html', {
        'kanban_data': kanban_data,
        'board_columns': board_columns
    })

@login_required
def job_list(request):
    jobs = JobPosting.objects.all()
    return render(request, 'hrms/job_list.html', {'jobs': jobs})

from .forms import JobPostingForm, CandidateForm
from .models import JobPosting, Candidate

@login_required
def job_create(request):
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hrms:job_list')
    else:
        form = JobPostingForm()
    return render(request, 'hrms/job_form.html', {'form': form, 'title': 'Create Job Posting'})

@login_required
def job_edit(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('hrms:job_list')
    else:
        form = JobPostingForm(instance=job)
    return render(request, 'hrms/job_form.html', {'form': form, 'title': 'Edit Job Posting', 'job': job})

@login_required
def candidate_create(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            
            # Workflow integration
            workflow, _ = Workflow.objects.get_or_create(
                name='ATS Pipeline Workflow', 
                defaults={'model_name': candidate.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(
                name='Applied', 
                workflow=workflow,
                defaults={'is_initial': True}
            )
            candidate.workflow_state = state
            candidate.status = 'Applied'
            candidate.save()
            return redirect('hrms:ats_dashboard')
    else:
        form = CandidateForm()
    return render(request, 'hrms/candidate_form.html', {'form': form, 'title': 'Add Candidate'})

@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Extract FSM target states
    fsm_map = candidate.__class__._get_fsm_transition_map()
    available_transitions = []
    
    for (source, target), method_name in fsm_map.items():
        if source == candidate.status or source == '*':
            available_transitions.append({
                'name': method_name.replace('_', ' ').title(),
                'target': target,
                'method': method_name
            })
            
    if request.method == 'POST':
        method_name = request.POST.get('method')
        if method_name:
            method = getattr(candidate, method_name)
            method()
            candidate.save(update_fields=['status'])
            
            workflow, _ = Workflow.objects.get_or_create(
                name='ATS Pipeline Workflow', 
                defaults={'model_name': candidate.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(name=candidate.status, workflow=workflow)
            candidate.workflow_state = state
            candidate.save(update_fields=['workflow_state'])
            
            return redirect('hrms:candidate_detail', pk=candidate.pk)
            
    return render(request, 'hrms/candidate_detail.html', {'candidate': candidate, 'available_transitions': available_transitions})

# --- Payroll Views ---

from .models import SalaryStructure, Payslip
from .forms import SalaryStructureForm
from .payslip_generator import generate_payslip_pdf
from django.http import FileResponse
from datetime import date
from django.contrib import messages

@login_required
def payroll_dashboard(request):
    payslips = Payslip.objects.select_related('employee__user').order_by('-month')
    return render(request, 'hrms/payroll_dashboard.html', {'payslips': payslips})

@login_required
def generate_payslips(request):
    """Generates payslips for the current month for all employees with a SalaryStructure."""
    if request.method == 'POST':
        today = date.today()
        current_month = date(today.year, today.month, 1)
        
        structures = SalaryStructure.objects.select_related('employee').all()
        count = 0
        for struct in structures:
            # Check if payslip already exists for this month
            if not Payslip.objects.filter(employee=struct.employee, month=current_month).exists():
                Payslip.objects.create(
                    employee=struct.employee,
                    month=current_month,
                    base_salary=struct.base_salary,
                    hra=struct.hra,
                    other_allowances=struct.other_allowances,
                    tax_deductions=struct.tax_deductions,
                    net_salary=struct.net_salary
                )
                count += 1
                
        messages.success(request, f"Successfully generated {count} payslips for {current_month.strftime('%B %Y')}.")
        return redirect('hrms:payroll_dashboard')
    
    return redirect('hrms:payroll_dashboard')

@login_required
def download_payslip_pdf(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    pdf_buffer = generate_payslip_pdf(payslip)
    
    filename = f"Payslip_{payslip.employee.user.first_name}_{payslip.month.strftime('%b_%Y')}.pdf"
    
    response = FileResponse(pdf_buffer, as_attachment=True, filename=filename)
    return response

@login_required
def edit_salary_structure(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    structure, created = SalaryStructure.objects.get_or_create(employee=employee)
    
    if request.method == 'POST':
        form = SalaryStructureForm(request.POST, instance=structure)
        if form.is_valid():
            form.save()
            messages.success(request, "Salary structure updated successfully.")
            return redirect('hrms:employee_detail', pk=employee.pk)
    else:
        form = SalaryStructureForm(instance=structure)
        
        
    return render(request, 'hrms/salary_structure_form.html', {'form': form, 'employee': employee})

# --- Appraisals & OKRs Views ---

from .models import PerformanceAppraisal, OKR
from .forms import PerformanceAppraisalForm, OKRForm

@login_required
def appraisal_list(request):
    appraisals = PerformanceAppraisal.objects.select_related('employee__user').all()
    return render(request, 'hrms/appraisal_list.html', {'appraisals': appraisals})

@login_required
def appraisal_create(request):
    if request.method == 'POST':
        form = PerformanceAppraisalForm(request.POST)
        if form.is_valid():
            appraisal = form.save(commit=False)
            
            workflow, _ = Workflow.objects.get_or_create(
                name='Performance Appraisal', 
                defaults={'model_name': appraisal.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(
                name='Draft', 
                workflow=workflow,
                defaults={'is_initial': True}
            )
            appraisal.workflow_state = state
            appraisal.status = 'Draft'
            appraisal.save()
            return redirect('hrms:appraisal_list')
    else:
        form = PerformanceAppraisalForm()
    return render(request, 'hrms/appraisal_form.html', {'form': form, 'title': 'Create Appraisal'})

@login_required
def appraisal_detail(request, pk):
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk)
    
    # Extract FSM target states
    fsm_map = appraisal.__class__._get_fsm_transition_map()
    available_transitions = []
    
    for (source, target), method_name in fsm_map.items():
        if source == appraisal.status or source == '*':
            available_transitions.append({
                'name': method_name.replace('_', ' ').title(),
                'target': target,
                'method': method_name
            })
            
    if request.method == 'POST':
        method_name = request.POST.get('method')
        if method_name:
            method = getattr(appraisal, method_name)
            method()
            appraisal.save(update_fields=['status'])
            
            workflow, _ = Workflow.objects.get_or_create(
                name='Performance Appraisal', 
                defaults={'model_name': appraisal.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(name=appraisal.status, workflow=workflow)
            appraisal.workflow_state = state
            appraisal.save(update_fields=['workflow_state'])
            
            messages.success(request, f"Appraisal moved to {appraisal.status}.")
            return redirect('hrms:appraisal_detail', pk=appraisal.pk)
            
    # Also fetch OKRs
    okrs = appraisal.okrs.all()
    
    # Check if form was submitted (saving form fields)
    if request.method == 'POST' and not request.POST.get('method'):
        form = PerformanceAppraisalForm(request.POST, instance=appraisal)
        if form.is_valid():
            form.save()
            messages.success(request, "Appraisal updated.")
            return redirect('hrms:appraisal_detail', pk=appraisal.pk)
    else:
        form = PerformanceAppraisalForm(instance=appraisal)
            
    return render(request, 'hrms/appraisal_detail.html', {
        'appraisal': appraisal, 
        'available_transitions': available_transitions,
        'okrs': okrs,
        'form': form
    })

@login_required
def okr_create(request, pk):
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk)
    if request.method == 'POST':
        form = OKRForm(request.POST)
        if form.is_valid():
            okr = form.save(commit=False)
            okr.appraisal = appraisal
            okr.save()
            messages.success(request, "OKR added successfully.")
            return redirect('hrms:appraisal_detail', pk=appraisal.pk)
    else:
        form = OKRForm()
    return render(request, 'hrms/okr_form.html', {'form': form, 'appraisal': appraisal})
