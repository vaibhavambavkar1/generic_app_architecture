from django.apps import AppConfig

class LogisticsFinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logistics_finance'
    verbose_name = 'Logistics Finance Integration'

    def ready(self):
        import logistics_finance.signals
