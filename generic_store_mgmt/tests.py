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
