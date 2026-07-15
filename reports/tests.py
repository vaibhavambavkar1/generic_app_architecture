from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from generic_store_mgmt.models import Product, UnitOfMeasure
from inventory.models import Warehouse, StockLedger
from sales.models import POSInvoice, POSLineItem
from finance.models import Account, AccountCategory, JournalEntry, JournalEntryLine

User = get_user_model()

class ReportsViewsTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='report_user', password='password123')
        self.client.force_login(self.user)
        
        from core.models import Organization
        Organization.objects.create(
            name="Test Org",
            owner_name="Test Owner",
            email="test@example.com"
        )
        
        # Base Data
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")
        self.product1 = Product.objects.create(name="Product A", uom=self.uom)
        self.product2 = Product.objects.create(name="Product B", uom=self.uom)
        self.warehouse = Warehouse.objects.create(name="Central Warehouse")
        
        # Finance Data
        self.inventory_acc = Account.objects.create(code='1200', name='Inventory Asset', category=AccountCategory.ASSET)
        self.ap_acc = Account.objects.create(code='2000', name='Accounts Payable', category=AccountCategory.LIABILITY)
        
        je = JournalEntry.objects.create(entry_number="JE-TEST-1", is_posted=True)
        JournalEntryLine.objects.create(journal_entry=je, account=self.inventory_acc, debit=Decimal("5000.00"))
        JournalEntryLine.objects.create(journal_entry=je, account=self.ap_acc, credit=Decimal("5000.00"))
        
        # Stock Data
        StockLedger.objects.create(
            product=self.product1, warehouse=self.warehouse, 
            transaction_type='OPENING', quantity=100
        )
        StockLedger.objects.create(
            product=self.product2, warehouse=self.warehouse, 
            transaction_type='OPENING', quantity=50
        )
        
        # Sales Data (Mocking past 7 days)
        invoice = POSInvoice.objects.create(
            invoice_number="INV-001", warehouse=self.warehouse,
            is_paid=True, total_amount=Decimal("1500.00")
        )
        # Override date to be within 30 days
        POSInvoice.objects.filter(pk=invoice.pk).update(date=timezone.now() - timedelta(days=2))
        
        POSLineItem.objects.create(
            invoice=invoice, product=self.product1,
            quantity=10, unit_price=Decimal("100.00"), line_total=Decimal("1000.00")
        )
        POSLineItem.objects.create(
            invoice=invoice, product=self.product2,
            quantity=5, unit_price=Decimal("100.00"), line_total=Decimal("500.00")
        )

    def test_executive_dashboard_view(self):
        url = reverse('reports:dashboard')
        response = self.client.get(url)
        if response.status_code == 302:
            print("REDIRECTING TO:", response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/executive_dashboard.html')
        
        # Check context
        self.assertEqual(response.context['revenue_30d'], Decimal("1500.00"))
        self.assertEqual(response.context['total_inventory_value'], Decimal("5000.00"))
        self.assertEqual(response.context['total_payables'], Decimal("5000.00"))
        
        # Check chart data exists
        self.assertIn('chart_labels', response.context)
        self.assertIn('chart_data', response.context)

    def test_sales_report_view(self):
        url = reverse('reports:sales_report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/sales_report.html')
        
        top_products = response.context['top_products']
        self.assertEqual(len(top_products), 2)
        
        # Product 1 should be first because line_total is 1000
        self.assertEqual(top_products[0]['product_name'], "Product A")
        self.assertEqual(top_products[0]['total_revenue'], Decimal("1000.00"))
        self.assertEqual(top_products[0]['total_sold'], 10)

    def test_inventory_report_view(self):
        url = reverse('reports:inventory_report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/inventory_report.html')
        
        stock_levels = response.context['stock_levels']
        self.assertEqual(len(stock_levels), 2)
        
        # Assert Product A has 100 stock
        prod_a_stock = next(s for s in stock_levels if s['product_name'] == "Product A")
        self.assertEqual(prod_a_stock['current_stock'], 100)
        self.assertEqual(prod_a_stock['warehouse_name'], "Central Warehouse")
