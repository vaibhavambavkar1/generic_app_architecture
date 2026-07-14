import hashlib
import json
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder

class ReportCache:
    """
    Caches calculated report results to improve performance and minimize DB load.
    """
    @staticmethod
    def generate_cache_key(report_id, config):
        # Serialize configuration dict to a deterministic string
        config_str = json.dumps(config, sort_keys=True, cls=DjangoJSONEncoder)
        config_hash = hashlib.md5(config_str.encode('utf-8')).hexdigest()
        return f"report_cache_{report_id}_{config_hash}"

    def get(self, cache_key):
        return cache.get(cache_key)

    def set(self, cache_key, data, timeout=300):
        """
        Default caching duration is 300 seconds (5 minutes).
        """
        cache.set(cache_key, data, timeout=timeout)
