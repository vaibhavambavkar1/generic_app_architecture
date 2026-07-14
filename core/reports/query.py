from .filters import FilterBuilder
from .grouping import GroupByBuilder
from .aggregate import AggregateBuilder
from .sorting import SortBuilder

class QueryBuilder:
    """
    Coordinates and builds the final Django ORM queryset by applying 
    filters, grouping, annotations/aggregates, and sorting.
    """
    def __init__(self, report):
        self.report = report
        self.queryset = report.get_base_queryset()

    def build(self, filters=None, group_by=None, aggregates=None, sorting=None):
        # 1. Apply Filters
        if filters:
            self.queryset = FilterBuilder().apply(self.queryset, filters)

        # 2. Apply Grouping
        if group_by:
            self.queryset = GroupByBuilder().apply(self.queryset, group_by)

        # 3. Apply Aggregates
        if aggregates:
            self.queryset = AggregateBuilder().apply(self.queryset, aggregates)

        # 4. Apply Sorting
        if sorting:
            self.queryset = SortBuilder().apply(self.queryset, sorting)

        return self.queryset
