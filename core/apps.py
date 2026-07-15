from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        """
        Core app initialization hook.
        Triggers auto-discovery of plugins.py and reports.py modules
        across all installed apps — no manual registration needed.
        """
        from core.sdk.registry import autodiscover_plugins
        autodiscover_plugins()
