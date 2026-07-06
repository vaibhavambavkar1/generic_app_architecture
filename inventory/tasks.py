from celery import shared_task
from django.db.models import F
from .models import Item
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_low_stock_alerts():
    """
    Periodically checks for items where stock_quantity falls below minimum_stock_level.
    """
    low_stock_items = Item.objects.filter(stock_quantity__lt=F('minimum_stock_level'))
    
    if not low_stock_items.exists():
        logger.info("No low stock items found.")
        return "No alerts sent."
        
    message = "The following items are running low on stock:\n\n"
    for item in low_stock_items:
        message += f"- {item.name} ({item.sku}): {item.stock_quantity} (Min: {item.minimum_stock_level})\n"
        
    # Simulate sending email for the MVP (this would use send_mail in production)
    logger.warning("CRITICAL LOW STOCK ALERT TRIGGERED:\n%s", message)
    
    return f"Sent alerts for {low_stock_items.count()} items."
