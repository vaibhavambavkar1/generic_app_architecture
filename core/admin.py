from django.contrib import admin
from .models import Workflow, State, Transition, ApprovalRoute

class StateInline(admin.TabularInline):
    model = State
    extra = 1

class TransitionInline(admin.TabularInline):
    model = Transition
    fk_name = 'workflow'
    extra = 1

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_name')
    search_fields = ('name', 'model_name')
    inlines = [StateInline, TransitionInline]

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'workflow', 'is_initial', 'is_final')
    list_filter = ('workflow', 'is_initial', 'is_final')

class ApprovalRouteInline(admin.TabularInline):
    model = ApprovalRoute
    extra = 1

from .models import Attachment

@admin.register(Transition)
class TransitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'workflow', 'from_state', 'to_state')
    list_filter = ('workflow',)
    inlines = [ApprovalRouteInline]

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'file_size', 'content_type', 'object_id', 'uploaded_at', 'uploaded_by')
    list_filter = ('content_type', 'uploaded_at')
    search_fields = ('filename',)
