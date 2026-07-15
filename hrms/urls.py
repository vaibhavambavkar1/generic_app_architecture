from django.urls import path
from . import views

app_name = 'hrms'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Employee Directory
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    
    # Leave Requests
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/create/', views.leave_create, name='leave_create'),
    path('leaves/<int:pk>/', views.leave_detail, name='leave_detail'),
    
    # Expense Claims
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    
    # ATS - Job Postings
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    
    # ATS - Candidates
    path('ats/', views.ats_dashboard, name='ats_dashboard'),
    path('candidates/create/', views.candidate_create, name='candidate_create'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    
    # Payroll
    path('payroll/', views.payroll_dashboard, name='payroll_dashboard'),
    path('payroll/generate/', views.generate_payslips, name='generate_payslips'),
    path('payroll/payslip/<int:pk>/pdf/', views.download_payslip_pdf, name='download_payslip_pdf'),
    path('employees/<int:pk>/salary/', views.edit_salary_structure, name='edit_salary_structure'),
    
    # Appraisals & OKRs
    path('appraisals/', views.appraisal_list, name='appraisal_list'),
    path('appraisals/create/', views.appraisal_create, name='appraisal_create'),
    path('appraisals/<int:pk>/', views.appraisal_detail, name='appraisal_detail'),
    path('appraisals/<int:pk>/okr/add/', views.okr_create, name='okr_create'),
]
