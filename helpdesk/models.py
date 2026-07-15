from django.db import models
from core.mixins import AuditableMixin
from core.models import WorkflowMixin
from django.contrib.auth import get_user_model
from django_fsm import transition
from django.utils import timezone

User = get_user_model()

class TicketCategory(AuditableMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Ticket(WorkflowMixin):
    """
    Helpdesk ticket with lifecycle states: Open -> In Progress -> Resolved -> Closed
    """
    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(TicketCategory, on_delete=models.RESTRICT, related_name='tickets')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_tickets')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    
    resolution_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    @transition(field='status', source='Open', target='In Progress')
    def assign_ticket(self, user):
        """Ticket assigned and being worked on."""
        self.assignee = user

    @transition(field='status', source=['Open', 'In Progress'], target='Resolved')
    def mark_resolved(self, notes=""):
        """Ticket issue resolved."""
        self.resolution_notes = notes

    @transition(field='status', source='Resolved', target='Closed')
    def close_ticket(self):
        """Ticket closed after confirmation."""
        pass

    @transition(field='status', source='*', target='Open')
    def reopen_ticket(self):
        """Ticket reopened."""
        pass

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"TKT-{self.id}: {self.title}"

class TicketComment(AuditableMixin):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_comments')
    body = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Visible only to staff/assignees")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on TKT-{self.ticket.id}"
