from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Asset, AssetCategory, AssetAssignment, MaintenanceRecord
from .forms import AssetForm, AssetCategoryForm, MaintenanceRecordForm
from core.models import State, Workflow

@login_required
def dashboard(request):
    total_assets = Asset.objects.count()
    in_use = Asset.objects.filter(status='In Use').count()
    available = Asset.objects.filter(status='Available').count()
    maintenance = Asset.objects.filter(status='Under Maintenance').count()
    
    categories = AssetCategory.objects.all()
    
    return render(request, 'itam/dashboard.html', {
        'total_assets': total_assets,
        'in_use': in_use,
        'available': available,
        'maintenance': maintenance,
        'categories': categories,
    })

@login_required
def asset_list(request):
    query = request.GET.get('q', '')
    if query:
        assets = Asset.objects.filter(name__icontains=query) | Asset.objects.filter(barcode__icontains=query)
    else:
        assets = Asset.objects.all()
    return render(request, 'itam/asset_list.html', {'assets': assets, 'query': query})

@login_required
def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            
            # Create workflow state
            workflow, _ = Workflow.objects.get_or_create(
                name='IT Asset Tracking', 
                defaults={'model_name': asset.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(
                name='Available', 
                workflow=workflow,
                defaults={'is_initial': True}
            )
            
            asset.workflow_state = state
            asset.status = 'Available'
            asset.save()
            messages.success(request, "Asset created successfully.")
            return redirect('itam:asset_list')
    else:
        form = AssetForm()
    return render(request, 'itam/asset_form.html', {'form': form, 'title': 'Add New Asset'})

@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    
    fsm_map = asset.__class__._get_fsm_transition_map()
    available_transitions = []
    
    for (source, target), method_name in fsm_map.items():
        if source == asset.status or source == '*':
            available_transitions.append({
                'name': method_name.replace('_', ' ').title(),
                'target': target,
                'method': method_name
            })
            
    if request.method == 'POST':
        method_name = request.POST.get('method')
        if method_name:
            if method_name == 'assign_asset':
                employee_id = request.POST.get('employee_id')
                if employee_id:
                    from hrms.models import Employee
                    employee = get_object_or_404(Employee, pk=employee_id)
                    asset.assign_asset(employee)
                    # Create assignment record
                    AssetAssignment.objects.create(asset=asset, employee=employee)
            elif method_name == 'return_asset':
                # Close the latest assignment
                assignment = asset.assignment_history.filter(returned_date__isnull=True).last()
                if assignment:
                    from datetime import date
                    assignment.returned_date = date.today()
                    assignment.save()
                asset.return_asset()
            elif method_name == 'send_to_maintenance':
                asset.send_to_maintenance()
            elif method_name == 'retire_asset':
                asset.retire_asset()

            asset.save(update_fields=['status', 'current_assignee'])
            
            # Sync workflow state
            workflow, _ = Workflow.objects.get_or_create(
                name='IT Asset Tracking', 
                defaults={'model_name': asset.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(name=asset.status, workflow=workflow)
            asset.workflow_state = state
            asset.save(update_fields=['workflow_state'])
            
            messages.success(request, f"Asset moved to {asset.status}.")
            return redirect('itam:asset_detail', pk=asset.pk)

    assignments = asset.assignment_history.all().order_by('-assigned_date')
    maintenance_records = asset.maintenance_records.all().order_by('-date')
    
    from hrms.models import Employee
    employees = Employee.objects.all()

    return render(request, 'itam/asset_detail.html', {
        'asset': asset,
        'available_transitions': available_transitions,
        'assignments': assignments,
        'maintenance_records': maintenance_records,
        'employees': employees
    })

from .barcode_generator import generate_asset_labels

@login_required
def export_asset_label(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return generate_asset_labels([asset])
