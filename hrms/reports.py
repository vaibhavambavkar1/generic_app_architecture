from core.reports.registry import BaseReport, ReportRegistry
from .models import LeaveRequest, ExpenseClaim, Employee

class LeaveBalanceReport(BaseReport):
    name = "Employee Leave Balances"
    description = "Current annual and sick leave balances for all employees."
    model = Employee

    def get_fields(self):
        return {
            'employee_id': 'Employee ID',
            'user__first_name': 'First Name',
            'user__last_name': 'Last Name',
            'department': 'Department',
            'annual_leave_balance': 'Annual Leave Remaining',
            'sick_leave_balance': 'Sick Leave Remaining'
        }

    def get_group_by_fields(self):
        return ['department']


class ExpenseSummaryReport(BaseReport):
    name = "Expense Summary Report"
    description = "Summary of employee expense claims and their statuses."
    model = ExpenseClaim

    def get_fields(self):
        return {
            'employee__user__first_name': 'First Name',
            'employee__user__last_name': 'Last Name',
            'title': 'Expense Title',
            'amount': 'Amount (Rs.)',
            'status': 'Status',
            'date_incurred': 'Date Incurred'
        }

    def get_group_by_fields(self):
        return ['status', 'employee__department']


ReportRegistry.register('leave_balance', LeaveBalanceReport)
ReportRegistry.register('expense_summary', ExpenseSummaryReport)
