from celery import shared_task
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

@shared_task
def write_audit_log(user_id, action, app_label, model_name, object_id, old_values, new_values):
    """
    Asynchronously writes to the AuditLog to prevent slowing down web requests.
    """
    from core.models import AuditLog
    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
    
    AuditLog.objects.create(
        user_id=user_id,
        action=action,
        content_type=content_type,
        object_id=object_id,
        old_values=old_values,
        new_values=new_values
    )
