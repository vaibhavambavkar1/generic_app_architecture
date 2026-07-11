from django.shortcuts import redirect
from django.urls import resolve
from django.core.cache import cache
from .license import LicenseManager

class LicenseEnforcementMiddleware:
    """Intercepts all requests and enforces an active, system-bound license."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            current_url_name = resolve(request.path_info).url_name
        except:
            current_url_name = None
        
        # Exempt specific routes to avoid redirect loops
        exempt_routes = ['login', 'activate_license', 'admin:login', 'logout']
        if current_url_name in exempt_routes or request.path.startswith('/static/'):
            return self.get_response(request)

        # Check license validity. Use a short-lived cache (60s) to avoid 
        # expensive RSA decoding on every single HTTP request.
        cache_key = "license_is_valid"
        is_valid = cache.get(cache_key)
        
        if is_valid is None:
            license_key = LicenseManager.get_current_license()
            valid, payload = LicenseManager.verify_license(license_key)
            is_valid = valid
            cache.set(cache_key, is_valid, timeout=60)
            
        if not is_valid:
            return redirect('core:activate_license')
            
        return self.get_response(request)


import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)

class ExceptionLoggingMiddleware:
    """Catches unhandled errors, logs them, and yields a clean HTMX error response or toast."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.error(f"Unhandled Exception: {str(exception)}", exc_info=True)
        
        if request.headers.get('HX-Request'):
            return render(request, 'core/auth/partials/error_message.html', {
                'error': f'An unexpected server error occurred: {str(exception)}'
            }, status=500)
            
        return None


import contextvars

_current_user = contextvars.ContextVar("current_user", default=None)

class ThreadLocalUserMiddleware:
    """Stores the current logged-in user in contextvars to make it accessible to models/mixins."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = None
        if request.user and request.user.is_authenticated:
            token = _current_user.set(request.user)
            
        try:
            response = self.get_response(request)
        finally:
            if token is not None:
                _current_user.reset(token)
                
        return response

def get_current_user():
    """Retrieve the current logged-in user from the request thread context."""
    return _current_user.get()


