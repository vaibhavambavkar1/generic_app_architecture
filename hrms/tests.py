from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Workflow, State, Organization
from hrms.models import Employee, LeaveRequest, ExpenseClaim, JobPosting, Candidate, SalaryStructure, Payslip, PerformanceAppraisal
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()

class HRMSTests(TestCase):
    def setUp(self):
        # Bypass Organization Setup redirect
        Organization.objects.create(
            name='Test Org',
            owner_name='Test Owner',
            email='test@example.com'
        )

        # Create a test user and manager
        self.manager_user = User.objects.create_user(username='manager', email='manager@example.com', password='testpassword')
        self.emp_user = User.objects.create_user(username='employee', email='emp@example.com', password='testpassword')
        
        self.client = Client()
        self.client.login(username='employee', password='testpassword')

        # Create Employees
        self.manager = Employee.objects.create(
            user=self.manager_user,
            employee_id='EMP-001',
            department='Management'
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            employee_id='EMP-002',
            department='Engineering',
            manager=self.manager,
            annual_leave_balance=20,
            sick_leave_balance=10
        )

        # Setup Workflows and States
        self.leave_wf = Workflow.objects.create(name='Leave Request', model_name='hrms.LeaveRequest')
        State.objects.create(name='Draft', workflow=self.leave_wf, is_initial=True)
        State.objects.create(name='Pending Manager', workflow=self.leave_wf)
        State.objects.create(name='Pending HR', workflow=self.leave_wf)
        State.objects.create(name='Approved', workflow=self.leave_wf)
        
        self.expense_wf = Workflow.objects.create(name='Expense Claim', model_name='hrms.ExpenseClaim')
        State.objects.create(name='Draft', workflow=self.expense_wf, is_initial=True)
        State.objects.create(name='Pending Manager', workflow=self.expense_wf)
        State.objects.create(name='Approved', workflow=self.expense_wf)

        self.ats_wf = Workflow.objects.create(name='ATS Pipeline Workflow', model_name='hrms.Candidate')
        State.objects.create(name='Applied', workflow=self.ats_wf, is_initial=True)
        State.objects.create(name='Phone Screen', workflow=self.ats_wf)

        self.appraisal_wf = Workflow.objects.create(name='Performance Appraisal', model_name='hrms.PerformanceAppraisal')
        State.objects.create(name='Draft', workflow=self.appraisal_wf, is_initial=True)
        State.objects.create(name='Self-Assessment', workflow=self.appraisal_wf)

        # Create base objects for testing details
        self.job = JobPosting.objects.create(
            title='Software Engineer',
            department='Engineering'
        )
        self.candidate = Candidate.objects.create(
            job=self.job,
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            status='Applied'
        )
        self.salary = SalaryStructure.objects.create(
            employee=self.employee,
            base_salary=Decimal('100000.00'),
            hra=Decimal('10000.00')
        )
        self.appraisal = PerformanceAppraisal.objects.create(
            employee=self.employee,
            review_period='Q1 2026',
            status='Draft'
        )

    # --- 1. Employee & Core HR Tests ---
    
    def test_employee_creation(self):
        self.assertEqual(self.employee.employee_id, 'EMP-002')
        self.assertEqual(self.employee.manager, self.manager)
        self.assertEqual(str(self.employee), ' (EMP-002)')
        
    def test_dashboard_view(self):
        response = self.client.get(reverse('hrms:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hrms/dashboard.html')

    # --- 2. Leave Management Tests ---
    
    def test_leave_request_workflow(self):
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type='Annual',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            reason='Vacation',
            status='Draft'
        )
        
        # Test transition to Manager
        leave.submit()
        self.assertEqual(leave.status, 'Pending Manager')
        
        # Test transition to HR
        leave.manager_approve()
        self.assertEqual(leave.status, 'Pending HR')
        
        # Test Final Approval & Balance Deduction
        initial_balance = self.employee.annual_leave_balance
        leave.hr_approve()
        self.assertEqual(leave.status, 'Approved')
        
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.annual_leave_balance, initial_balance - 3)

    # --- 3. Expense Claims Tests ---
    
    def test_expense_claim_workflow(self):
        expense = ExpenseClaim.objects.create(
            employee=self.employee,
            title='Client Dinner',
            amount=Decimal('500.00'),
            date_incurred=date.today(),
            status='Draft'
        )
        
        expense.submit()
        self.assertEqual(expense.status, 'Pending Manager')

    # --- 4. ATS / Recruitment Tests ---
    
    def test_ats_dashboard_view(self):
        response = self.client.get(reverse('hrms:ats_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('kanban_data', response.context)
        
    def test_candidate_workflow(self):
        self.candidate.schedule_phone_screen()
        self.assertEqual(self.candidate.status, 'Phone Screen')

    # --- 5. Payroll Tests ---
    
    def test_salary_structure_calculation(self):
        self.assertEqual(self.salary.net_salary, Decimal('110000.00'))
        
    def test_generate_payslips_view(self):
        # Generate payslips via POST
        response = self.client.post(reverse('hrms:generate_payslips'))
        self.assertEqual(response.status_code, 302)  # Redirect to payroll dashboard
        
        # Verify a payslip was created for the employee
        current_month = date(date.today().year, date.today().month, 1)
        self.assertTrue(Payslip.objects.filter(employee=self.employee, month=current_month).exists())
        
        payslip = Payslip.objects.get(employee=self.employee, month=current_month)
        self.assertEqual(payslip.net_salary, Decimal('110000.00'))

    # --- 6. Performance Appraisals Tests ---
    
    def test_appraisal_workflow(self):
        self.appraisal.start_self_assessment()
        self.assertEqual(self.appraisal.status, 'Self-Assessment')
        
    def test_appraisal_list_view(self):
        response = self.client.get(reverse('hrms:appraisal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hrms/appraisal_list.html')
