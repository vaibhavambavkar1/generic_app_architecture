from core.sdk.registry import BasePlugin, PluginRegistry

class CRMPlugin(BasePlugin):
    identifier = "crm"
    name = "CRM & Sales"
    description = "Lead tracking and pipeline management."

    def get_menu_items(self):
        # Menu items are hardcoded in the sidebar template under a specific section
        return []

PluginRegistry.register(CRMPlugin)
