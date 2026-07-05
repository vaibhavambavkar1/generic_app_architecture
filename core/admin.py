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

@admin.register(Transition)
class TransitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'workflow', 'from_state', 'to_state')
    list_filter = ('workflow',)
    inlines = [ApprovalRouteInline]
