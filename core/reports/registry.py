from django.db import models

class BaseReport:
    """
    Base class for defining a report.
    Plugins subclass this to register their own reports.
    """
    name = ""
    description = ""
    model = None  # Django model class
    permission_required = None  # Permission codename string or list of groups

    def get_base_queryset(self):
        """Returns the initial queryset for the report."""
        if self.model:
            return self.model.objects.all()
        raise NotImplementedError("Report must define a model or override get_base_queryset.")

    def get_fields(self):
        """
        Returns a dict of available fields: { 'field_name': 'Label' }
        """
        return {}

    def get_filters(self):
        """
        Returns a list of available filter config definitions.
        """
        return []

    def get_group_by_fields(self):
        """
        Returns a list of fields allowed for grouping.
        """
        return []

    def get_aggregates(self):
        """
        Returns a list of allowed aggregate functions.
        """
        return ['sum', 'avg', 'min', 'max', 'count']


class ReportRegistry:
    """
    Registry pattern manager to register and retrieve report providers.
    """
    _reports = {}

    @classmethod
    def register(cls, report_id, report_class):
        if not issubclass(report_class, BaseReport):
            raise ValueError("Report class must inherit from BaseReport")
        cls._reports[report_id] = report_class()

    @classmethod
    def get_report(cls, report_id):
        report = cls._reports.get(report_id)
        if not report:
            raise KeyError(f"Report '{report_id}' is not registered.")
        return report

    @classmethod
    def get_all_reports(cls):
        return cls._reports
