class GroupByBuilder:
    """
    Applies values() to group the QuerySet results by specific fields.
    """
    def apply(self, queryset, group_by_fields):
        if not group_by_fields:
            return queryset
        
        # Coerce to a list of strings if string is passed
        if isinstance(group_by_fields, str):
            group_by_fields = [group_by_fields]

        return queryset.values(*group_by_fields)
