class PermissionChecker:
    """
    Ensures users are authorized to view specific reports and filters out 
    restricted fields based on role privileges.
    """
    def check_report_permission(self, user, report):
        if user.is_superuser:
            return True

        perm = getattr(report, 'permission_required', None)
        if not perm:
            return True

        # Check standard permission strings
        if isinstance(perm, str):
            return user.has_perm(perm)
        
        # Check list/tuple of required Groups
        if isinstance(perm, (list, tuple)):
            return user.groups.filter(name__in=perm).exists()

        return False

    def filter_visible_fields(self, user, report, fields):
        """
        Optionally filters list of fields based on field-level permission rules.
        Example: report.restricted_fields = { 'unit_price': 'inventory.view_sensitive_pricing' }
        """
        restricted = getattr(report, 'restricted_fields', {})
        if not restricted or user.is_superuser:
            return fields

        visible_fields = []
        for f in fields:
            req_perm = restricted.get(f)
            if not req_perm or user.has_perm(req_perm):
                visible_fields.append(f)
        return visible_fields
