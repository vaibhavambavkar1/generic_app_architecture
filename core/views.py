from django.shortcuts import get_object_or_404, render
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest
from django.db import transaction

from .models import Transition

@login_required
@require_POST
@transaction.atomic
def execute_transition(request, app_label, model_name, object_id, transition_id):
    """
    Generic HTMX endpoint to execute a workflow transition on any model.
    """
    try:
        model_class = apps.get_model(app_label, model_name)
    except LookupError:
        return HttpResponseBadRequest("Invalid model")

    instance = get_object_or_404(model_class, id=object_id)
    transition = get_object_or_404(Transition, id=transition_id)

    try:
        instance.transition_to(transition, request.user)
        toast_message = f"Successfully transitioned to {transition.to_state.name}"
        toast_type = 'success'
    except ValueError as e:
        toast_message = str(e)
        toast_type = 'error'

    context = {
        'instance': instance,
        'transitions': instance.get_available_transitions(request.user),
        'app_label': app_label,
        'model_name': model_name,
        'toast_message': toast_message,
        'toast_type': toast_type,
        'is_transition_response': True,
    }
    response = render(request, 'core/components/workflow/action_buttons.html', context)
    
    if toast_type == 'success' and model_name.lower() == 'purchaseorder' and transition.to_state.name in ['Approved', 'Received']:
        import json
        from django.urls import reverse
        download_url = reverse('inventory:po_download_pdf', args=[instance.id])
        response['HX-Trigger'] = json.dumps({
            "showReceiptPrompt": {"url": download_url}
        })
        
    return response

from django.http import FileResponse, HttpResponse
from .backup import BackupManager

@login_required
def backup_dashboard(request):
    """Admin dashboard for managing database backups."""
    if request.method == 'POST':
        if 'backup_file' not in request.FILES:
            return HttpResponse("No file provided", status=400)
            
        file = request.FILES['backup_file']
        if not file.name.endswith('.json'):
            context = {'toast_message': "Invalid format. Must be JSON.", 'toast_type': 'error'}
            return render(request, 'core/backup_dashboard.html', context)
            
        success, message = BackupManager.restore_backup(file)
        
        context = {
            'toast_message': message,
            'toast_type': 'success' if success else 'error'
        }
        return render(request, 'core/backup_dashboard.html', context)
        
    return render(request, 'core/backup_dashboard.html')

@login_required
def download_backup(request):
    """Streams a database backup download."""
    buffer, filename = BackupManager.create_backup()
    return FileResponse(buffer, as_attachment=True, filename=filename)

from .models import SystemConfig

@login_required
def settings_dashboard(request):
    """Unified dashboard for configurations, rules, and backups."""
    configs = SystemConfig.objects.all().order_by('key')
    org = Organization.objects.first()
    return render(request, 'core/settings_dashboard.html', {
        'configs': configs,
        'org': org
    })

@login_required
@require_POST
def update_config(request, pk):
    config = get_object_or_404(SystemConfig, pk=pk)
    try:
        new_val_str = request.POST.get('value')
        import json
        new_val = json.loads(new_val_str)
        config.value = new_val
        config.save()
        
        from django.core.cache import cache
        cache.delete(f"sysconfig_{config.key}")
        
        return HttpResponse(f'<span class="text-green-600 font-bold ml-2">Saved!</span>')
    except Exception as e:
        return HttpResponse(f'<span class="text-red-600 ml-2">Error: {str(e)}</span>', status=400)

from .license import LicenseManager
from .config import Config
from django.shortcuts import redirect

def activate_license(request):
    """View for displaying and processing license activation."""
    hwid = LicenseManager.get_hardware_id()
    
    if request.method == 'POST':
        key = request.POST.get('license_key')
        valid, msg = LicenseManager.verify_license(key)
        
        if valid:
            # Save valid license to the DB Config store
            Config.set('APP_LICENSE_KEY', key, 'Global System License Key (JWT)')
            
            # Invalidate the middleware cache immediately
            from django.core.cache import cache
            cache.delete("license_is_valid")
            
            return redirect('/')
        else:
            return render(request, 'core/activate_license.html', {'hwid': hwid, 'error': msg})
            
    return render(request, 'core/activate_license.html', {'hwid': hwid})


from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

@login_required
def profile_view(request):
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('core:profile')
            
        elif action == 'change_password':
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Keep session active
                messages.success(request, "Password changed successfully.")
                return redirect('core:profile')
            else:
                return render(request, 'core/profile.html', {
                    'password_form': form,
                    'active_tab': 'password'
                })
                
    password_form = PasswordChangeForm(user)
    return render(request, 'core/profile.html', {
        'password_form': password_form,
        'active_tab': 'profile'
    })

from .forms import OrganizationForm
from .models import Organization

@login_required
def organization_setup(request):
    """View to setup or edit the single Organization instance."""
    org = Organization.objects.first()
    is_new = org is None
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, "Organization details saved successfully.")
            return redirect('core:settings_dashboard')
    else:
        form = OrganizationForm(instance=org)
        
    return render(request, 'core/organization_form.html', {
        'form': form,
        'is_new': is_new,
        'org': org
    })


from core.reports.registry import ReportRegistry
from core.reports.engine import ReportEngine, ChartBuilder
from core.reports.exporter import ReportExporter
from core.models import SavedReport
from django.contrib import messages
from django.shortcuts import redirect
import json

@login_required
def report_builder(request):
    """
    Renders the dynamic report builder dashboard, showing the select module dropdown
    and saved reports list.
    """
    reports = ReportRegistry.get_all_reports()
    saved_reports = SavedReport.objects.all().order_by('-created_at')
    
    edit_report = None
    edit_id = request.GET.get('edit')
    if edit_id:
        try:
            edit_report = SavedReport.objects.get(pk=edit_id)
        except SavedReport.DoesNotExist:
            return redirect('core:report_builder')
        
    return render(request, 'core/reports/builder.html', {
        'reports': reports,
        'saved_reports': saved_reports,
        'edit_report': edit_report
    })

@login_required
def load_report_fields(request):
    """
    HTMX view returning fields, filters, group by and aggregates builders
    for the selected report.
    """
    report_id = request.GET.get('report_id')
    saved_report_id = request.GET.get('saved_report_id')
    
    saved_config = {}
    if saved_report_id:
        saved_report = get_object_or_404(SavedReport, pk=saved_report_id)
        # Check if the user selected a different report from the dropdown
        if not report_id or report_id == saved_report.report_id:
            report_id = saved_report.report_id
            saved_config = saved_report.config
        else:
            # Module changed - drop the saved report editing context and load clean state for the new module
            saved_report_id = None
        
    if not report_id:
        return HttpResponse("")
        
    try:
        report = ReportRegistry.get_report(report_id)
    except KeyError:
        return HttpResponse("Report not found", status=404)
        
    return render(request, 'core/reports/partials/config_form.html', {
        'report_id': report_id,
        'report': report,
        'fields': report.get_fields(),
        'group_by_fields': report.get_group_by_fields(),
        'aggregates': report.get_aggregates(),
        'saved_config': saved_config,
        'saved_report_id': saved_report_id
    })

@login_required
def add_filter_row(request):
    """
    HTMX view adding an inline filter input row dynamically.
    """
    report_id = request.GET.get('report_id')
    report = ReportRegistry.get_report(report_id)
    index = int(request.GET.get('index', 0))
    
    return render(request, 'core/reports/partials/filter_row.html', {
        'index': index,
        'fields': report.get_fields(),
        'operators': [
            ('eq', 'Equals'),
            ('ne', 'Not Equals'),
            ('gt', 'Greater Than'),
            ('gte', 'Greater Than or Equal'),
            ('lt', 'Less Than'),
            ('lte', 'Less Than or Equal'),
            ('contains', 'Contains'),
        ]
    })

@login_required
def add_aggregate_row(request):
    """
    HTMX view adding an inline aggregate input row dynamically.
    """
    report_id = request.GET.get('report_id')
    report = ReportRegistry.get_report(report_id)
    index = int(request.GET.get('index', 0))
    
    return render(request, 'core/reports/partials/aggregate_row.html', {
        'index': index,
        'fields': report.get_fields(),
        'functions': [
            ('sum', 'Sum'),
            ('avg', 'Average'),
            ('min', 'Minimum'),
            ('max', 'Maximum'),
            ('count', 'Count'),
        ]
    })

def _parse_report_config(request):
    """
    Helper to extract report configurations from request post parameters.
    """
    fields = request.POST.getlist('fields')
    
    # Parse Filters
    filters = []
    filter_fields = request.POST.getlist('filter_field')
    filter_ops = request.POST.getlist('filter_operator')
    filter_vals = request.POST.getlist('filter_value')
    for i in range(len(filter_fields)):
        if filter_fields[i] and filter_ops[i]:
            val = filter_vals[i]
            # Coerce boolean strings
            if val.lower() == 'true':
                val = True
            elif val.lower() == 'false':
                val = False
            elif val.isdigit():
                val = int(val)
            else:
                try:
                    val = float(val)
                except ValueError:
                    pass
            filters.append({
                'field': filter_fields[i],
                'operator': filter_ops[i],
                'value': val
            })
            
    # Parse Group By
    group_by = request.POST.getlist('group_by')
    
    # Parse Aggregates
    aggregates = []
    agg_fields = request.POST.getlist('agg_field')
    agg_funcs = request.POST.getlist('agg_function')
    agg_aliases = request.POST.getlist('agg_alias')
    for i in range(len(agg_fields)):
        if agg_fields[i] and agg_funcs[i] and agg_aliases[i]:
            aggregates.append({
                'field': agg_fields[i],
                'function': agg_funcs[i],
                'alias': agg_aliases[i]
            })
            
    # Parse Formulas
    formulas = {}
    formula_aliases = request.POST.getlist('formula_alias')
    formula_exprs = request.POST.getlist('formula_expression')
    for i in range(len(formula_aliases)):
        if formula_aliases[i] and formula_exprs[i]:
            formulas[formula_aliases[i]] = formula_exprs[i]
            
    # Parse Sorting
    sorting = []
    sort_field = request.POST.get('sort_field')
    sort_dir = request.POST.get('sort_direction', 'asc')
    if sort_field:
        sorting.append({'field': sort_field, 'direction': sort_dir})
        
    return {
        'fields': fields,
        'filters': filters,
        'group_by': group_by,
        'aggregates': aggregates,
        'formulas': formulas,
        'sorting': sorting
    }

@login_required
def report_preview(request):
    """
    HTMX endpoint that builds and executes the report, yielding an HTML table preview.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")
        
    report_id = request.POST.get('report_id')
    config = _parse_report_config(request)
    
    engine = ReportEngine()
    try:
        data = engine.execute(report_id, request.user, config, use_cache=False)
        report = ReportRegistry.get_report(report_id)
        
        # Determine headers for preview table
        headers = {}
        if config.get('group_by') or config.get('aggregates'):
            # Group by and aggregate field headers
            for g in config.get('group_by'):
                headers[g] = report.get_fields().get(g, g)
            for agg in config.get('aggregates'):
                headers[agg['alias']] = f"{agg['function'].upper()}({agg['field']}) as {agg['alias']}"
        else:
            for f in config.get('fields'):
                headers[f] = report.get_fields().get(f, f)
                
        for alias in config.get('formulas', {}).keys():
            headers[alias] = f"Formula: {alias}"
            
        saved_report_id = request.POST.get('saved_report_id')
        saved_report_name = ""
        if saved_report_id:
            try:
                saved_report_name = SavedReport.objects.get(pk=saved_report_id).name
            except SavedReport.DoesNotExist:
                pass

        return render(request, 'core/reports/partials/preview_table.html', {
            'data': data,
            'headers': headers,
            'report_id': report_id,
            'config_json': json.dumps(config),
            'saved_report_id': saved_report_id,
            'saved_report_name': saved_report_name
        })
    except Exception as e:
        return render(request, 'core/reports/partials/processing_status.html', {
            'message': "Processing configuration... Adjusting parameters to match the selected module's schema. Please configure fields to preview."
        })

@login_required
@require_POST
def save_report(request):
    """
    Saves or updates a report configuration in the database.
    """
    name = request.POST.get('report_name')
    report_id = request.POST.get('report_id')
    config_json = request.POST.get('config_json')
    saved_report_id = request.POST.get('saved_report_id')
    
    if not name or not report_id or not config_json:
        return render(request, 'core/auth/partials/error_message.html', {
            'error': "Missing required inputs to save the report."
        })
        
    try:
        config = json.loads(config_json)
        if saved_report_id:
            # Update existing report
            saved_report = get_object_or_404(SavedReport, pk=saved_report_id)
            saved_report.name = name
            saved_report.config = config
            saved_report.save()
            msg = "Report configuration updated successfully!"
        else:
            # Create new report
            SavedReport.objects.create(
                name=name,
                report_id=report_id,
                config=config,
                created_by=request.user
            )
            msg = "Report configuration saved successfully!"
        
        saved_reports = SavedReport.objects.all().order_by('-created_at')
        response = render(request, 'core/reports/partials/saved_reports_list.html', {
            'saved_reports': saved_reports,
            'toast_message': msg,
            'toast_type': 'success'
        })
        response['HX-Trigger'] = 'reportSaved'
        return response
    except Exception as e:
        return render(request, 'core/auth/partials/error_message.html', {
            'error': f"Failed to save report: {str(e)}"
        })

@login_required
def execute_saved_report(request, pk):
    """
    Renders/executes a saved report by its primary key.
    """
    saved_report = get_object_or_404(SavedReport, pk=pk)
    report_id = saved_report.report_id
    config = saved_report.config
    
    engine = ReportEngine()
    try:
        data = engine.execute(report_id, request.user, config, use_cache=True)
        report = ReportRegistry.get_report(report_id)
        
        # Build headers
        headers = {}
        if config.get('group_by') or config.get('aggregates'):
            for g in config.get('group_by'):
                headers[g] = report.get_fields().get(g, g)
            for agg in config.get('aggregates'):
                headers[agg['alias']] = agg['alias']
        else:
            for f in config.get('fields'):
                headers[f] = report.get_fields().get(f, f)
                
        for alias in config.get('formulas', {}).keys():
            headers[alias] = alias

        return render(request, 'core/reports/runner.html', {
            'saved_report': saved_report,
            'data': data,
            'headers': headers,
            'report_id': report_id,
            'config_json': json.dumps(config)
        })
    except Exception as e:
        return render(request, 'core/auth/partials/error_message.html', {
            'error': f"Failed to run report: {str(e)}"
        })

@login_required
def export_report(request):
    """
    Export current report state to CSV, Excel, PDF, or JSON.
    """
    report_id = request.GET.get('report_id')
    export_format = request.GET.get('format', 'csv')
    config_str = request.GET.get('config')
    
    if not report_id or not config_str:
        return HttpResponseBadRequest("Missing required report parameters.")
        
    try:
        config = json.loads(config_str)
        engine = ReportEngine()
        data = engine.execute(report_id, request.user, config, use_cache=True)
        report = ReportRegistry.get_report(report_id)
        
        # Build headers mapping
        headers = {}
        if config.get('group_by') or config.get('aggregates'):
            for g in config.get('group_by'):
                headers[g] = report.get_fields().get(g, g)
            for agg in config.get('aggregates'):
                headers[agg['alias']] = agg['alias']
        else:
            for f in config.get('fields'):
                headers[f] = report.get_fields().get(f, f)
        for alias in config.get('formulas', {}).keys():
            headers[alias] = alias

        filename = f"report_{report_id}"
        
        if export_format == 'csv':
            buf = ReportExporter.to_csv(data, headers)
            response = HttpResponse(buf.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            return response
            
        elif export_format == 'excel':
            buf = ReportExporter.to_excel(data, headers)
            response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
            return response
            
        elif export_format == 'pdf':
            buf = ReportExporter.to_pdf(data, headers, title=report.name)
            response = HttpResponse(buf.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response
            
        elif export_format == 'json':
            buf = ReportExporter.to_json(data)
            response = HttpResponse(buf.getvalue(), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
            return response
            
        return HttpResponseBadRequest("Unsupported format")
    except Exception as e:
        return HttpResponse(f"Export failed: {str(e)}", status=500)


@login_required
@require_POST
def delete_saved_report(request, pk):
    """
    Deletes a saved report configuration from the database.
    """
    saved_report = get_object_or_404(SavedReport, pk=pk)
    saved_report.delete()
    
    # Check if the deleted report is currently being edited in the Referer URL
    referer = request.META.get('HTTP_REFERER', '')
    if f'?edit={pk}' in referer or f'&edit={pk}' in referer:
        response = HttpResponse("")
        from django.urls import reverse
        response['HX-Redirect'] = reverse('core:report_builder')
        return response
        
    saved_reports = SavedReport.objects.all().order_by('-created_at')
    return render(request, 'core/reports/partials/saved_reports_list.html', {
        'saved_reports': saved_reports,
        'toast_message': "Report configuration deleted successfully!",
        'toast_type': 'success'
    })


from django_tables2 import SingleTableView
from .tables import AuditLogTable
from .models import AuditLog

class AuditLogListView(SingleTableView):
    model = AuditLog
    table_class = AuditLogTable
    template_name = "core/audit_logs.html"
    paginated_by = 15


@login_required
def global_search(request):
    """
    Unified global search queries across Suppliers, Products, and Purchase Orders.
    Returns results dynamically to the topbar search dropdown.
    """
    from django.db import models
    from inventory.models import Supplier, InventoryItem, PurchaseOrder

    query = request.GET.get('q', '').strip()
    results = {
        'items': [],
        'suppliers': [],
        'pos': []
    }
    if query:
        # Search InventoryItem
        results['items'] = InventoryItem.objects.filter(
            models.Q(name__icontains=query) | models.Q(sku__icontains=query)
        ).order_by('name')[:5]

        # Search Supplier
        results['suppliers'] = Supplier.objects.filter(
            models.Q(name__icontains=query) | models.Q(contact_email__icontains=query) | models.Q(phone__icontains=query)
        ).order_by('name')[:5]

        # Search PurchaseOrder
        results['pos'] = PurchaseOrder.objects.filter(
            po_number__icontains=query
        ).order_by('-created_at')[:5]


    return render(request, 'core/components/search_results.html', {
        'results': results,
        'query': query
    })

from .models import Workflow, Transition, ApprovalRoute
from django.contrib.auth.models import Group

@login_required
def workflow_dashboard(request):
    """
    Administrative dashboard to manage Workflows, Transitions, and RBAC / Guardian configurations.
    """
    # Fetch all workflows with their states and transitions
    workflows = Workflow.objects.prefetch_related('states', 'transitions__approvals').all()
    
    return render(request, 'core/workflow_dashboard.html', {
        'workflows': workflows
    })

@login_required
@require_POST
def update_approval_route(request, transition_id):
    """
    HTMX view to update the RBAC settings (Group / Guardian Permission) for a transition.
    """
    transition = get_object_or_404(Transition, id=transition_id)
    
    # We assume one approval route per transition for this simple dashboard
    approval_route, created = ApprovalRoute.objects.get_or_create(transition=transition)
    
    group_id = request.POST.get('required_group')
    permission = request.POST.get('required_permission')
    
    if group_id:
        approval_route.required_group_id = group_id
    else:
        approval_route.required_group = None
        
    approval_route.required_permission = permission or ''
    approval_route.save()
    
    # Return the updated row fragment
    groups = Group.objects.all()
    return render(request, 'core/components/workflow/transition_row.html', {
        'transition': transition,
        'route': approval_route,
        'groups': groups
    })

@login_required
def edit_transition_row(request, transition_id):
    """
    HTMX view to render the inline edit form for a transition's RBAC settings.
    """
    transition = get_object_or_404(Transition, id=transition_id)
    approval_route = transition.approvals.first()
    groups = Group.objects.all()
    
    return render(request, 'core/components/workflow/transition_row_edit.html', {
        'transition': transition,
        'route': approval_route,
        'groups': groups
    })

@login_required
def cancel_edit_transition_row(request, transition_id):
    """
    HTMX view to render the read-only row for a transition.
    """
    transition = get_object_or_404(Transition, id=transition_id)
    approval_route = transition.approvals.first()
    groups = Group.objects.all()
    
    return render(request, 'core/components/workflow/transition_row.html', {
        'transition': transition,
        'route': approval_route,
        'groups': groups
    })

from .models import ChatMessage

@login_required
def chat_messages(request):
    """HTMX endpoint to return latest chat messages."""
    messages = ChatMessage.objects.filter(recipient__isnull=True).order_by('-timestamp')[:50]
    messages = reversed(messages)
    return render(request, 'core/components/chat_messages_list.html', {'chat_messages': messages})

@login_required
@require_POST
def send_chat_message(request):
    """HTMX endpoint to send a new chat message."""
    content = request.POST.get('message', '').strip()
    if content:
        ChatMessage.objects.create(
            sender=request.user,
            recipient=None,
            content=content
        )
    messages = ChatMessage.objects.filter(recipient__isnull=True).order_by('-timestamp')[:50]
    messages = reversed(messages)
    return render(request, 'core/components/chat_messages_list.html', {'chat_messages': messages})
