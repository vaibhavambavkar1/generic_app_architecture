import django_tables2 as tables
from .models import AuditLog

class AuditLogTable(tables.Table):
    class Meta:
        model = AuditLog
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = ("timestamp", "user", "action", "content_type", "object_id", "old_values", "new_values")
        attrs = {
            "class": "table table-xs w-full text-base-content bg-base-200 shadow-md rounded-xl overflow-hidden",
            "thead": {
                "class": "bg-base-300 font-semibold"
            }
        }
