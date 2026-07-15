from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import HttpResponse

from .models import Customer, Lead
from .forms import CustomerForm, LeadForm
from core.models import State

@login_required
def dashboard(request):
    """
    CRM Dashboard view showing pipeline metrics.
    """
    total_customers = Customer.objects.count()
    active_leads = Lead.objects.exclude(status__in=['Won', 'Lost']).count()
    pipeline_value = Lead.objects.exclude(status__in=['Won', 'Lost']).aggregate(Sum('value'))['value__sum'] or 0.00
    won_leads = Lead.objects.filter(status='Won').count()
    
    # Kanban board data
    board_columns = ['Draft', 'Contacted', 'Qualified', 'Proposal', 'Won', 'Lost']
    kanban_data = {}
    for col in board_columns:
        kanban_data[col] = Lead.objects.filter(status=col).select_related('customer')
        
    return render(request, 'crm/dashboard.html', {
        'total_customers': total_customers,
        'active_leads': active_leads,
        'pipeline_value': pipeline_value,
        'won_leads': won_leads,
        'kanban_data': kanban_data,
        'board_columns': board_columns
    })

# --- Customer Views ---

@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    if query:
        customers = Customer.objects.filter(name__icontains=query)
    else:
        customers = Customer.objects.all()
    return render(request, 'crm/customer_list.html', {'customers': customers, 'query': query})

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            return redirect('crm:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'crm/customer_form.html', {'form': form, 'title': 'Add Customer'})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('crm:customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'crm/customer_form.html', {'form': form, 'title': 'Edit Customer', 'customer': customer})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    leads = customer.leads.all()
    return render(request, 'crm/customer_detail.html', {'customer': customer, 'leads': leads})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('crm:customer_list')
    return render(request, 'crm/customer_confirm_delete.html', {'customer': customer})

# --- Lead Views ---

@login_required
def lead_list(request):
    query = request.GET.get('q', '')
    if query:
        leads = Lead.objects.filter(title__icontains=query).select_related('customer')
    else:
        leads = Lead.objects.all().select_related('customer')
    return render(request, 'crm/lead_list.html', {'leads': leads, 'query': query})

@login_required
def lead_create(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            
            # Find or create a Workflow and Draft state
            from core.models import Workflow, State
            workflow, _ = Workflow.objects.get_or_create(
                name='Lead Workflow', 
                defaults={'model_name': lead.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(
                name='Draft', 
                workflow=workflow,
                defaults={'is_initial': True}
            )
                
            lead.workflow_state = state
            lead.status = 'Draft'
            lead.save()
            return redirect('crm:dashboard')
    else:
        form = LeadForm()
    return render(request, 'crm/lead_form.html', {'form': form, 'title': 'Add Lead'})

@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect('crm:lead_list')
    else:
        form = LeadForm(instance=lead)
    return render(request, 'crm/lead_form.html', {'form': form, 'title': 'Edit Lead', 'lead': lead})

@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    
    # Manually extract FSM target states for UI buttons
    fsm_map = lead.__class__._get_fsm_transition_map()
    available_transitions = []
    
    for (source, target), method_name in fsm_map.items():
        if source == lead.status or source == '*':
            available_transitions.append({
                'name': method_name.replace('mark_', '').replace('_', ' ').title(),
                'target': target,
                'method': method_name
            })
            
    if request.method == 'POST':
        method_name = request.POST.get('method')
        if method_name:
            # Execute transition
            method = getattr(lead, method_name)
            method()
            lead.save(update_fields=['status'])
            
            # also sync workflow state if it exists
            from core.models import Workflow, State
            workflow, _ = Workflow.objects.get_or_create(
                name='Lead Workflow', 
                defaults={'model_name': lead.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(name=lead.status, workflow=workflow)
            lead.workflow_state = state
            lead.save(update_fields=['workflow_state'])
            
            return redirect('crm:lead_detail', pk=lead.pk)

    return render(request, 'crm/lead_detail.html', {
        'lead': lead,
        'available_transitions': available_transitions
    })

@login_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.delete()
        return redirect('crm:lead_list')
    return render(request, 'crm/lead_confirm_delete.html', {'lead': lead})

@login_required
def lead_transition_modal(request, pk, transition_id):
    """Placeholder HTMX transition modal if we want full WorkflowMixin transition_to."""
    pass

@login_required
def lead_transition_submit(request, pk, transition_id):
    """Placeholder HTMX transition submit if we want full WorkflowMixin transition_to."""
    pass
