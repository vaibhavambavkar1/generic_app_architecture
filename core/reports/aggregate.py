from django.db.models import Sum, Avg, Min, Max, Count

class AggregateBuilder:
    """
    Applies annotations for aggregate functions (Sum, Avg, Min, Max, Count) to the QuerySet.
    """
    AGG_MAP = {
        'sum': Sum,
        'avg': Avg,
        'min': Min,
        'max': Max,
        'count': Count
    }

    def apply(self, queryset, aggregates_config):
        """
        aggregates_config should be a list of dicts:
        [
            {'field': 'field_to_aggregate', 'function': 'sum|avg|min|max|count', 'alias': 'annotated_field_name'},
            ...
        ]
        """
        annotations = {}
        for agg in aggregates_config:
            field = agg.get('field')
            func_name = agg.get('function', '').lower()
            alias = agg.get('alias')

            if not field or not func_name or not alias:
                continue

            agg_class = self.AGG_MAP.get(func_name)
            if agg_class:
                annotations[alias] = agg_class(field)

        if annotations:
            queryset = queryset.annotate(**annotations)

        return queryset
