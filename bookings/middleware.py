from .models import BusinessProfile

class TenantMiddleware:
    """
    Middleware to resolve the active BusinessProfile (Tenant) based on the request.
    In a production SaaS, this would parse the Host header (subdomains) 
    or check a specific X-Tenant-ID header for API calls.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check header (Useful for REST APIs and headless clients)
        tenant_header = request.headers.get('X-Tenant-ID')
        
        # Check Host for subdomain (e.g., clinic.saas.com)
        host = request.get_host().split(':')[0]
        
        tenant = None
        if tenant_header:
            tenant = BusinessProfile.objects.filter(id=tenant_header, is_active=True).first()
        else:
            # For this MVP, we fall back to the first active profile if not explicitly provided
            # A true multi-tenant system would raise a 404 or redirect to a landing page if tenant not found.
            tenant = BusinessProfile.objects.filter(is_active=True).first()
            
        request.tenant = tenant
        
        response = self.get_response(request)
        return response
