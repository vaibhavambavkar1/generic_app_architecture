from django.core.cache import cache
from .models import SystemConfig

class Config:
    """Helper service to fetch and set dynamic system configurations with caching."""
    
    @staticmethod
    def get(key, default=None):
        cache_key = f"sysconfig_{key}"
        val = cache.get(cache_key)
        if val is not None:
            return val
            
        try:
            val = SystemConfig.objects.get(key=key).value
            cache.set(cache_key, val, timeout=3600) # Cache for 1 hour
            return val
        except SystemConfig.DoesNotExist:
            return default

    @staticmethod
    def set(key, value, description=""):
        obj, created = SystemConfig.objects.update_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        cache.set(f"sysconfig_{key}", value, timeout=3600)
        return obj
