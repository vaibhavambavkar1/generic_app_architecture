from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .events import EventBus, workflow_transitioned
from .rules.registry import RuleEngine

class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name="Organization/Company Name")
    owner_name = models.CharField(max_length=150, verbose_name="Owner Name")
    address = models.TextField(blank=True, verbose_name="Address")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Contact/Phone Number")
    gstin = models.CharField(max_length=15, blank=True, null=True, verbose_name="GSTIN Number")
    license_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="License Number")
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True, verbose_name="Organization Logo")

    class Meta:
        verbose_name = "Organization Details"
        verbose_name_plural = "Organization Details"

    def clean(self):
        # Enforce singleton pattern: only one record allowed
        if not self.pk and Organization.objects.exists():
            raise ValidationError("Only one Organization can be registered.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Workflow(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    model_name = models.CharField(
        max_length=100, 
        help_text="e.g., 'inventory.PurchaseOrder'"
    )

    def __str__(self):
        return self.name

class State(models.Model):
    workflow = models.ForeignKey(Workflow, related_name='states', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    class Meta:
        unique_together = ('workflow', 'name')

    def __str__(self):
        return f"{self.workflow.name} - {self.name}"

class Transition(models.Model):
    workflow = models.ForeignKey(Workflow, related_name='transitions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    from_state = models.ForeignKey(State, related_name='outgoing_transitions', on_delete=models.CASCADE)
    to_state = models.ForeignKey(State, related_name='incoming_transitions', on_delete=models.CASCADE)
    
    # Comma-separated list of conditions registered in RuleEngine
    conditions = models.CharField(max_length=255, blank=True, help_text="Comma-separated condition names")
    
    # Comma-separated list of actions registered in RuleEngine
    actions = models.CharField(max_length=255, blank=True, help_text="Comma-separated action names")

    class Meta:
        unique_together = ('workflow', 'from_state', 'to_state', 'name')

    def __str__(self):
        return f"{self.name} ({self.from_state.name} -> {self.to_state.name})"

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.content_type} #{self.object_id} at {self.timestamp}"

class ApprovalLog(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transition = models.ForeignKey(Transition, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.approver} - {self.transition.name} on {self.content_object}"



class ApprovalRoute(models.Model):
    transition = models.ForeignKey(Transition, related_name='approvals', on_delete=models.CASCADE)
    required_group = models.ForeignKey('auth.Group', on_delete=models.SET_NULL, null=True, blank=True)
    required_permission = models.CharField(max_length=255, blank=True, help_text="e.g., 'inventory.approve_purchaseorder'")
    
    def can_approve(self, user, obj=None):
        if self.required_permission:
            # Guardian: Check for object-level permission, or global permission
            if obj and user.has_perm(self.required_permission, obj):
                return True
            if user.has_perm(self.required_permission):
                return True
            return False
            
        if self.required_group:
            return user.groups.filter(id=self.required_group.id).exists()
            
        return True

from core.mixins import AuditableMixin
from django_fsm import FSMField

class WorkflowMixin(AuditableMixin):
    """
    Abstract mixin for fat models to integrate with the Workflow Engine.
    
    FSM method mappings are cached at the class level via __init_subclass__
    to avoid expensive dir() introspection on every transition call.
    """
    workflow_state = models.ForeignKey(
        State, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_instances'
    )
    status = FSMField(default='Draft')
    
    # Class-level cache: {(source_state, target_state): method_name}
    _fsm_transition_map = None
    
    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs):
        """
        Hook called when a concrete model subclasses WorkflowMixin.
        Builds a cached mapping of FSM-decorated methods keyed by
        (source_state, target_state) for O(1) lookup during transitions.
        """
        super().__init_subclass__(**kwargs)
        # Defer cache building — the class may not be fully defined yet.
        # We'll build it lazily on first use via _get_fsm_transition_map().
        cls._fsm_transition_map = None

    @classmethod
    def _get_fsm_transition_map(cls):
        """
        Lazily builds and caches the FSM transition map for this model class.
        Returns dict: {(source_state, target_state): method_name}
        """
        if cls._fsm_transition_map is not None:
            return cls._fsm_transition_map

        transition_map = {}
        for attr_name in dir(cls):
            try:
                attr = getattr(cls, attr_name)
            except AttributeError:
                continue
            if callable(attr) and hasattr(attr, '_django_fsm'):
                transitions_dict = attr._django_fsm.transitions
                for source, transition_meta in transitions_dict.items():
                    transition_map[(source, transition_meta.target)] = attr_name

        cls._fsm_transition_map = transition_map
        return transition_map

    def get_workflow_name(self):
        """Derive the workflow identifier based on the model name."""
        return f"{self._meta.app_label}.{self.__class__.__name__}"
        
    def get_available_transitions(self, user):
        """Return a list of transitions available from the current state for the given user."""
        if not self.workflow_state:
            return []
            
        transitions = self.workflow_state.outgoing_transitions.all()
        available = []
        for transition in transitions:
            # Check approval route
            approvals = transition.approvals.all()
            can_approve = True
            for approval in approvals:
                if not approval.can_approve(user, obj=self):
                    can_approve = False
                    break
            
            if can_approve:
                available.append(transition)
                
        return available

    def transition_to(self, transition, user, **context_kwargs):
        """
        Attempt to execute a transition on this instance.
        Evaluates conditions, updates state, emits event, and executes actions.
        """
        if transition not in self.get_available_transitions(user):
            raise ValueError(f"Transition {transition.name} is not available for user {user}.")
            
        context = {
            'instance': self,
            'user': user,
            'transition': transition
        }
        context.update(context_kwargs)
        
        # 1. Evaluate Conditions (Rule Engine)
        if transition.conditions:
            condition_names = [c.strip() for c in transition.conditions.split(',')]
            for cond_name in condition_names:
                if not RuleEngine.evaluate_condition(cond_name, context):
                    raise ValueError(f"Condition '{cond_name}' failed for transition '{transition.name}'.")
                    
        # 2. State Change
        old_state = self.workflow_state
        self.workflow_state = transition.to_state
        
        # Execute django-fsm transition if one exists (O(1) cached lookup)
        source_state_name = old_state.name if old_state else 'Draft'
        self.status = source_state_name  # Ensure FSM state is synchronized
        target_state_name = transition.to_state.name
        
        fsm_map = self.__class__._get_fsm_transition_map()
        fsm_method_name = fsm_map.get((source_state_name, target_state_name))
        if not fsm_method_name:
            # Fallback: check wildcard source ('*')
            fsm_method_name = fsm_map.get(('*', target_state_name))
        
        if fsm_method_name:
            fsm_method = getattr(self, fsm_method_name)
            fsm_method()  # Call the fsm decorated method
        else:
            self.status = target_state_name
            
        if user:
            self._audit_user_id = user.id
        self.save(update_fields=['workflow_state', 'status'])
        
        # 3. Emit Event (Event Bus)
        EventBus.publish(
            workflow_transitioned, 
            sender=self.__class__, 
            instance=self, 
            old_state=old_state, 
            new_state=self.workflow_state, 
            user=user
        )
        
        # 4. Execute Actions (Rule Engine)
        if transition.actions:
            action_names = [a.strip() for a in transition.actions.split(',')]
            for act_name in action_names:
                RuleEngine.execute_action(act_name, context)

class SystemConfig(models.Model):
    key = models.CharField(max_length=100, unique=True, help_text="e.g., REQUIRE_PO_APPROVAL")
    value = models.JSONField(help_text="Store values as JSON (e.g., true, 100, \"string\")")
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "System Configurations"
        
    def __str__(self):
        return f"{self.key}: {self.value}"

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    security_question = models.CharField(max_length=255, blank=True)
    security_answer_hash = models.CharField(max_length=255, blank=True)
    
    def set_security_answer(self, raw_answer):
        from django.contrib.auth.hashers import make_password
        self.security_answer_hash = make_password(raw_answer.strip().lower())
        self.save()
        
    def check_security_answer(self, raw_answer):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_answer.strip().lower(), self.security_answer_hash)
        
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class BaseMasterData(AuditableMixin):
    """
    Abstract base model representing core Master Data (e.g. Customers, Suppliers, Products).
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name} ({self.code})"


class BaseCatalogItem(AuditableMixin):
    """
    Abstract base model representing catalog items mapping suppliers/clients to products.
    """
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class BaseInventoryItem(BaseMasterData):
    """
    Abstract base model representing inventory items with stock tracking features.
    """
    stock_level = models.IntegerField(default=0)
    reorder_threshold = models.IntegerField(default=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        abstract = True


class Attachment(AuditableMixin):
    """
    Generic reusable Attachment model linked to any entity via ContentTypes.
    """
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes", blank=True, null=True)
    
    # Generic relationship fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='uploaded_attachments'
    )

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if self.file and not self.filename:
            import os
            self.filename = os.path.basename(self.file.name)
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.filename} ({self.file_size} bytes) attached to {self.content_type.model} #{self.object_id}"


class SavedReport(AuditableMixin):
    """
    Model to store configured report parameters so they can be re-run or pinned to dashboards.
    """
    name = models.CharField(max_length=255)
    report_id = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='saved_reports'
    )

    def __str__(self):
        return f"{self.name} ({self.report_id})"

class PaymentMethod(AuditableMixin):
    """
    Master data for Payment Methods (Cash, UPI, Card, etc.) configurable for the ERP.
    """
    PAYMENT_TYPES = (
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('BANK', 'Bank Transfer'),
        ('WALLET', 'Digital Wallet'),
        ('OTHER', 'Other'),
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=15, choices=PAYMENT_TYPES)
    is_active = models.BooleanField(default=True)
    # Allows storing dynamic gateway details, UPI handles, etc. without hardcoding fields
    configuration = models.JSONField(blank=True, default=dict, help_text="Specific configs like UPI ID, Merchant ID, API keys, etc.")
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class PaymentTransaction(AuditableMixin):
    """
    Generic model to track payments made or received across the entire application (Sales, Purchases, HRMS, etc.)
    """
    TRANSACTION_TYPES = (
        ('IN', 'Inbound (Receipt)'),
        ('OUT', 'Outbound (Payment)'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='IN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS')
    
    # Generic relation to link to POSInvoice, SalesOrder, PurchaseOrder, Payroll, etc.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    reference_number = models.CharField(max_length=100, blank=True, help_text="External reference like UTR or Gateway ID")
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} ({self.get_transaction_type_display()}) via {self.payment_method.name}"

