from core.sdk.registry import BasePlugin, PluginRegistry

class BookingsPlugin(BasePlugin):
    identifier = "bookings"
    name = "Bookings & Scheduling"
    description = "Manage schedules, resources, and appointments across various industries."

    def get_menu_items(self):
        return [
            {"label": "Dashboard", "url": "/bookings/"},
            {"label": "Calendar", "url": "/bookings/calendar/"},
            {"label": "Resources", "url": "/bookings/resources/"},
            {"label": "Schedules", "url": "/bookings/schedules/"},
            {"label": "Reports", "url": "/bookings/reports/"},
            {"label": "Setup Wizard", "url": "/bookings/setup/"},
        ]

# Auto-register when this module is imported by autodiscover_plugins()
PluginRegistry.register(BookingsPlugin)
