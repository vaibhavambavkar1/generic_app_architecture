from core.reports.registry import BaseReport, ReportRegistry
from .models import Lead, Customer

class LeadPipelineReport(BaseReport):
    name = "Lead Pipeline Report"
    description = "Analysis of current CRM leads and their estimated value."
    model = Lead

    def get_fields(self):
        return {
            'title': 'Deal Name',
            'customer__name': 'Customer',
            'value': 'Estimated Value (Rs.)',
            'status': 'Current Status',
            'expected_close_date': 'Expected Close Date'
        }

    def get_group_by_fields(self):
        return ['status', 'customer__name']


class CustomerDirectoryReport(BaseReport):
    name = "Customer Directory Report"
    description = "List of all active CRM customers."
    model = Customer

    def get_fields(self):
        return {
            'name': 'Customer Name',
            'email': 'Email',
            'phone': 'Phone',
            'industry': 'Industry',
            'is_active': 'Active Status'
        }

    def get_group_by_fields(self):
        return ['industry', 'is_active']


ReportRegistry.register('lead_pipeline', LeadPipelineReport)
ReportRegistry.register('customer_directory', CustomerDirectoryReport)
