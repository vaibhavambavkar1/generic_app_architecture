from django.db.models import Q

class FilterBuilder:
    """
    Applies validated filtering conditions to a Django QuerySet.
    Supported operators: eq, ne, gt, gte, lt, lte, contains, in
    """
    OPERATOR_MAP = {
        'eq': '',
        'gt': '__gt',
        'gte': '__gte',
        'lt': '__lt',
        'lte': '__lte',
        'contains': '__icontains',
        'in': '__in',
    }

    def apply(self, queryset, filters_config):
        """
        filters_config is expected to be a list of dicts:
        [
            {'field': 'field_name', 'operator': 'operator_name', 'value': value},
            ...
        ]
        """
        for cond in filters_config:
            field = cond.get('field')
            operator = cond.get('operator')
            value = cond.get('value')

            if not field or not operator:
                continue

            if operator == 'ne':
                # Not Equal maps to django exclude
                queryset = queryset.exclude(**{field: value})
            elif operator in self.OPERATOR_MAP:
                lookup = f"{field}{self.OPERATOR_MAP[operator]}"
                queryset = queryset.filter(**{lookup: value})

        return queryset
