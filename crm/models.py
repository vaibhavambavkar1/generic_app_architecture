from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django_fsm import transition

class Customer(AuditableMixin):
    """
    Master data for a Customer (Company or Individual).
    """
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Lead(WorkflowMixin):
    """
    Pipeline lead tracking model utilizing WorkflowMixin.
    States typically: Draft (New) -> Contacted -> Qualified -> Proposal -> Won/Lost
    """
    title = models.CharField(max_length=200, help_text="Short description of the deal")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='leads')
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Estimated deal value")
    expected_close_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    @transition(field='status', source='Draft', target='Contacted')
    def mark_contacted(self):
        """Lead has been contacted."""
        pass

    @transition(field='status', source='Contacted', target='Qualified')
    def mark_qualified(self):
        """Lead is qualified."""
        pass

    @transition(field='status', source='Qualified', target='Proposal')
    def send_proposal(self):
        """Proposal sent to the lead."""
        pass

    @transition(field='status', source=['Draft', 'Contacted', 'Qualified', 'Proposal'], target='Won')
    def mark_won(self):
        """Deal won."""
        pass

    @transition(field='status', source=['Draft', 'Contacted', 'Qualified', 'Proposal'], target='Lost')
    def mark_lost(self):
        """Deal lost."""
        pass

    def __str__(self):
        return f"{self.title} - {self.customer.name}"
