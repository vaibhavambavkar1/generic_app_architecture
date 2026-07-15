from core.sdk.registry import BasePlugin, PluginRegistry

class HRMSPlugin(BasePlugin):
    identifier = "hrms"
    name = "HRMS"
    description = "Human Resources Management System."

    def get_menu_items(self):
        # Menu items are hardcoded in the sidebar template under a specific section
        return []

PluginRegistry.register(HRMSPlugin)
