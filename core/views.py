from django.shortcuts import get_object_or_404, render
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest

from .models import Transition

@login_required
@require_POST
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
        'toast_type': toast_type
    }
    
    return render(request, 'core/components/workflow_actions.html', context)

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
    return render(request, 'core/settings_dashboard.html', {'configs': configs})

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

