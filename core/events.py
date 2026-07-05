from django.dispatch import Signal

# ---------------------------------------------------------
# Core Business Events
# ---------------------------------------------------------
# Fired when a new document/record is created
document_created = Signal()

# Fired when a document/record is updated
document_updated = Signal()

# Fired when a document/record changes workflow state
workflow_transitioned = Signal()


class EventBus:
    """
    Centralized event bus wrapper over Django signals.
    Provides a standardized way to emit events across the system.
    """
    @staticmethod
    def publish(event_signal, sender, **kwargs):
        """
        Publish an event to the bus.
        
        :param event_signal: The Signal instance to send.
        :param sender: The model class or identifier sending the event.
        :param kwargs: Additional context (e.g., instance, user, metadata).
        """
        event_signal.send(sender=sender, **kwargs)
