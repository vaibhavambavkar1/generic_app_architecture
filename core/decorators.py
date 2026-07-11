from functools import wraps
from django.core.cache import cache
from django.shortcuts import render

def ratelimit_custom(rate="5/m"):
    """
    Custom decorator to rate limit POST requests.
    rate format: 'number/period' (e.g. '5/m' for 5 requests per minute, '10/h')
    """
    limit, period = rate.split('/')
    limit = int(limit)
    
    seconds_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    period_seconds = seconds_map.get(period.lower(), 60)
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method == 'POST':
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
                cache_key = f"rl_{view_func.__name__}_{ip}"
                
                request_count = cache.get(cache_key, 0)
                if request_count >= limit:
                    return render(request, 'core/auth/partials/error_message.html', {
                        'error': 'Too many requests. Please wait a minute before trying again.'
                    }, status=429)
                
                cache.set(cache_key, request_count + 1, timeout=period_seconds)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
