from .registry import ReportRegistry
from .query import QueryBuilder
from .formulas import FormulaEngine
from .permissions import PermissionChecker
from .cache import ReportCache
from core.models import AuditLog
from django.contrib.contenttypes.models import ContentType

class AuditLogger:
    """
    Records report executions in the system's AuditLog.
    """
    @staticmethod
    def log_report_execution(user, report, config):
        try:
            model_ct = ContentType.objects.get_for_model(report.model)
            # Log the execution event
            AuditLog.objects.create(
                user=user,
                action='UPDATE',  # Read action logged as UPDATE to track security audits
                content_type=model_ct,
                object_id=0,
                old_values={'report_name': report.name, 'config': config},
                new_values={'status': 'executed'}
            )
        except Exception:
            pass


class ChartBuilder:
    """
    Aggregates and formats raw report data into formats readable by Chart.js/Plotly.
    """
    @staticmethod
    def build_chart_data(data, label_field, value_field):
        labels = []
        values = []
        for row in data:
            labels.append(str(row.get(label_field, '')))
            try:
                values.append(float(row.get(value_field, 0.0)))
            except (ValueError, TypeError):
                values.append(0.0)
        return {
            'labels': labels,
            'datasets': [{
                'label': value_field,
                'data': values
            }]
        }


class ReportEngine:
    """
    Coordinates permissions, caching, ORM builders, formula execution, 
    and audit logging to compile final reports.
    """
    def __init__(self):
        self.permission_checker = PermissionChecker()
        self.cache_manager = ReportCache()

    def execute(self, report_id, user, config=None, use_cache=True):
        if config is None:
            config = {}

        report = ReportRegistry.get_report(report_id)

        # 1. Verify access permissions
        if not self.permission_checker.check_report_permission(user, report):
            raise PermissionError(f"User {user.username} is not authorized to run report '{report.name}'.")

        # 2. Check Cache
        cache_key = self.cache_manager.generate_cache_key(report_id, config)
        if use_cache:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                AuditLogger.log_report_execution(user, report, config)
                return cached_data

        # 3. Construct Query
        builder = QueryBuilder(report)
        queryset = builder.build(
            filters=config.get('filters'),
            group_by=config.get('group_by'),
            aggregates=config.get('aggregates'),
            sorting=config.get('sorting')
        )

        # Determine visible fields based on permissions
        fields = config.get('fields')
        if not fields:
            fields = list(report.get_fields().keys())
        visible_fields = self.permission_checker.filter_visible_fields(user, report, fields)

        # Fetch records
        if config.get('group_by') or config.get('aggregates'):
            # If grouping is applied, fields are already limited/coerced by GroupByBuilder/values
            data = list(queryset)
        else:
            data = list(queryset.values(*visible_fields))

        # 4. Process computed fields (formulas)
        data = FormulaEngine.apply_formulas(data, config.get('formulas'))

        # 5. Populate Cache
        if use_cache:
            self.cache_manager.set(cache_key, data, timeout=config.get('cache_timeout', 300))

        # 6. Audit Execution
        AuditLogger.log_report_execution(user, report, config)

        return data
