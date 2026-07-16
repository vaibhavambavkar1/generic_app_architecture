from django.test import TestCase
from decimal import Decimal
from django.db.utils import IntegrityError
from .models import Category, Brand, UnitOfMeasure, TaxBracket, Product, PriceList, PriceListItem

class GenericStoreMgmtModelTests(TestCase):
    
    def setUp(self):
        # Create foundational records
        self.brand = Brand.objects.create(name="TestBrand", description="A test brand")
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")
        
        self.tax = TaxBracket.objects.create(
            name="GST 18%", 
            cgst_rate=Decimal("9.00"), 
            sgst_rate=Decimal("9.00"), 
            igst_rate=Decimal("18.00")
        )
        
        self.category_parent = Category.objects.create(name="Electronics")
        self.category_child = Category.objects.create(name="Mobiles", parent=self.category_parent)

    def test_tax_bracket_total_rate(self):
        """Test the property total_rate calculation for TaxBracket"""
        self.assertEqual(self.tax.total_rate, Decimal("18.00"))

    def test_category_str_representation(self):
        """Test that Category string representation shows parent > child"""
        self.assertEqual(str(self.category_parent), "Electronics")
        self.assertEqual(str(self.category_child), "Electronics > Mobiles")
        
    def test_product_auto_sku_generation(self):
        """Test that a Product gets an auto-generated SKU if none is provided"""
        product = Product.objects.create(
            name="Test Mobile Phone",
            brand=self.brand,
            uom=self.uom,
            category=self.category_child,
            tax_bracket=self.tax,
            purchase_price=Decimal("10000.00"),
            selling_price=Decimal("12000.00")
        )
        
        self.assertIsNotNone(product.sku)
        self.assertTrue(product.sku.startswith("PROD-"))
        self.assertEqual(len(product.sku), 13) # "PROD-" + 8 chars

    def test_product_manual_sku(self):
        """Test that a Product keeps its manually provided SKU"""
        manual_sku = "CUST-SKU-999"
        product = Product.objects.create(
            name="Manual SKU Product",
            sku=manual_sku,
            uom=self.uom,
        )
        self.assertEqual(product.sku, manual_sku)
        
    def test_price_list_unique_constraint(self):
        """Test that a product cannot be added twice to the same PriceList"""
        price_list = PriceList.objects.create(name="Wholesale")
        product = Product.objects.create(name="Bulk Item", uom=self.uom)
        
        # Add successfully
        PriceListItem.objects.create(price_list=price_list, product=product, rate=Decimal("50.00"))
        
        # Add duplicate should raise IntegrityError
        with self.assertRaises(IntegrityError):
            PriceListItem.objects.create(price_list=price_list, product=product, rate=Decimal("45.00"))

from django.urls import reverse
from django.contrib.auth import get_user_model

class GenericStoreMgmtModalTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password123')
        self.client.force_login(self.user)
        from core.models import Organization
        Organization.objects.create(name="Test Org", owner_name="Owner", email="owner@test.com")
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")

    def test_product_create_modal_get(self):
        url = reverse('generic_store_mgmt:product_create_modal')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertTemplateUsed(response, 'generic_store_mgmt/product_form_modal.html')

    def test_product_create_modal_post_success(self):
        url = reverse('generic_store_mgmt:product_create_modal')
        data = {
            'name': 'New Modal Product',
            'sku': 'SKU-MODAL-1',
            'product_type': 'goods',
            'uom': self.uom.id,
            'purchase_price': '10.00',
            'selling_price': '20.00',
            'manage_stock': True,
            'is_active': True,
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        self.assertTrue(Product.objects.filter(sku='SKU-MODAL-1').exists())
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertEqual(response['HX-Refresh'], 'true')

    def test_product_edit_modal_get(self):
        product = Product.objects.create(name="To Edit", uom=self.uom)
        url = reverse('generic_store_mgmt:product_edit_modal', args=[product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertTemplateUsed(response, 'generic_store_mgmt/product_form_modal.html')

    def test_product_edit_modal_post_success(self):
        product = Product.objects.create(name="To Edit", uom=self.uom, sku='OLD-SKU')
        url = reverse('generic_store_mgmt:product_edit_modal', args=[product.id])
        data = {
            'name': 'Edited Product Name',
            'sku': 'OLD-SKU',
            'product_type': 'goods',
            'uom': self.uom.id,
            'purchase_price': '15.00',
            'selling_price': '25.00',
            'manage_stock': True,
            'is_active': True,
        }
        response = self.client.post(url, data, HTTP_HX_REQUEST='true')
        
        product.refresh_from_db()
        self.assertEqual(product.name, 'Edited Product Name')
        self.assertEqual(response.status_code, 200, getattr(response, 'url', 'No URL'))
        self.assertEqual(response['HX-Refresh'], 'true')
