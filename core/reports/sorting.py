class SortBuilder:
    """
    Applies ordering to a Django QuerySet.
    Supports either string notation (e.g., ['-field_name']) or dict notation.
    """
    def apply(self, queryset, sort_config):
        """
        sort_config can be:
        - A list of strings: ['field1', '-field2']
        - A list of dicts: [{'field': 'field1', 'direction': 'asc'}, {'field': 'field2', 'direction': 'desc'}]
        """
        if not sort_config:
            return queryset

        ordering = []
        if isinstance(sort_config, list):
            for item in sort_config:
                if isinstance(item, str):
                    ordering.append(item)
                elif isinstance(item, dict):
                    field = item.get('field')
                    direction = item.get('direction', 'asc').lower()
                    if field:
                        prefix = '-' if direction == 'desc' else ''
                        ordering.append(f"{prefix}{field}")

        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset
