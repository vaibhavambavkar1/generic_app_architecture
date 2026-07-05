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
