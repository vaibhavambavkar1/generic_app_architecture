import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

class AuditableMixin(models.Model):
    """
    Mixin to automatically generate audit logs on model save.
    Usage: Inherit this alongside models.Model.
    Important: Set `_audit_user_id` on the instance before save to track the user.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from core.tasks import write_audit_log
        
        is_new = self.pk is None
        action = 'CREATE' if is_new else 'UPDATE'
        
        old_values = {}
        new_values = {}
        
        from django.db.models.fields.files import FieldFile
        
        if not is_new:
            # We need to get the old values from DB to diff them
            cls = self.__class__
            old_instance = cls.objects.get(pk=self.pk)
            
            for field in cls._meta.fields:
                field_name = field.attname
                old_val = getattr(old_instance, field_name)
                new_val = getattr(self, field_name)
                
                if isinstance(old_val, FieldFile):
                    old_val = old_val.name if old_val else None
                if isinstance(new_val, FieldFile):
                    new_val = new_val.name if new_val else None
                
                if old_val != new_val:
                    old_values[field_name] = old_val
                    new_values[field_name] = new_val
        else:
            for field in self._meta.fields:
                val = getattr(self, field.attname)
                if isinstance(val, FieldFile):
                    val = val.name if val else None
                new_values[field.attname] = val

        # Proceed with normal save
        super().save(*args, **kwargs)
        
        # Only log if something changed or it's new
        if new_values:
            # Serialize dates and decimals safely
            old_json = json.loads(json.dumps(old_values, cls=DjangoJSONEncoder))
            new_json = json.loads(json.dumps(new_values, cls=DjangoJSONEncoder))
            
            user_id = getattr(self, '_audit_user_id', None)
            if not user_id:
                from core.middleware import get_current_user
                curr_user = get_current_user()
                if curr_user:
                    user_id = curr_user.id
            
            # Dispatch to Celery instantly
            write_audit_log.delay(
                user_id=user_id,
                action=action,
                app_label=self._meta.app_label,
                model_name=self._meta.model_name,
                object_id=self.pk,
                old_values=old_json,
                new_values=new_json
            )
