from django import template

register = template.Library()

@register.inclusion_tag('core/components/workflow_actions.html', takes_context=True)
def render_workflow_actions(context, instance):
    """
    Renders the workflow transition buttons for a given instance.
    Automatically checks permissions based on the logged-in user.
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return {'instance': instance, 'transitions': []}
        
    available_transitions = instance.get_available_transitions(request.user)
    return {
        'instance': instance,
        'transitions': available_transitions,
        'app_label': instance._meta.app_label,
        'model_name': instance._meta.model_name,
        'csrf_token': context.get('csrf_token'),
    }
