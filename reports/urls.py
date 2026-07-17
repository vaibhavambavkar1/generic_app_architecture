from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.executive_dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('finance/', views.finance_reports_hub, name='finance_reports_hub'),
    path('finance/trial-balance/', views.trial_balance, name='trial_balance'),
    path('finance/general-ledger/', views.general_ledger, name='general_ledger'),
    path('finance/income-statement/', views.income_statement, name='income_statement'),
    path('finance/balance-sheet/', views.balance_sheet, name='balance_sheet'),
]
