import os
import django
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_framework.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Organization, UserProfile
from hotel_core.models import HotelBranch
from hotel_pos.models import MenuCategory, MenuItem, Table, Order, OrderItem, CashierShift
from inventory.models import InventoryItem, Warehouse
from hotel_recipes.models import Recipe, RecipeItem

def seed():
    print("Clearing old data...")
    Order.objects.all().delete()
    MenuItem.objects.all().delete()
    MenuCategory.objects.all().delete()
    Table.objects.all().delete()
    HotelBranch.objects.all().delete()
    Organization.objects.all().delete()
    InventoryItem.objects.all().delete()
    Recipe.objects.all().delete()
    
    print("Seeding Hotel Management Data...")
    
    # 1. Organization & Branch
    org, _ = Organization.objects.get_or_create(
        name="Grand Hotel & Resorts",
        owner_name="Admin",
        email="admin@grandhotel.com",
        phone="555-0100"
    )
    
    branch = HotelBranch.objects.create(
        name="Downtown Grand",
        code="DTG",
        address="123 Main St, Downtown",
        contact_number="555-0101",
        organization=org
    )
    
    # 2. Warehouse & Inventory
    warehouse, _ = Warehouse.objects.get_or_create(
        name="Main Kitchen Store",
        location="Downtown Grand - Basement"
    )
    
    inv_chicken = InventoryItem.objects.create(
        name="Chicken Breast", sku="ING-CHK-01",
        stock_level=50, unit_price=Decimal("5.50")
    )
    inv_flour = InventoryItem.objects.create(
        name="All Purpose Flour", sku="ING-FLR-01",
        stock_level=100, unit_price=Decimal("1.20")
    )
    inv_tomato = InventoryItem.objects.create(
        name="Fresh Tomatoes", sku="ING-TOM-01",
        stock_level=30, unit_price=Decimal("2.00")
    )
    
    # 3. Tables
    tables = []
    for i in range(1, 11):
        tables.append(Table.objects.create(
            branch=branch, number=str(i), capacity=random.choice([2, 4, 6])
        ))
        
    # 4. Menu & Recipes
    cat_mains = MenuCategory.objects.create(name="Main Course", branch=branch, description="Delicious main dishes")
    cat_drinks = MenuCategory.objects.create(name="Beverages", branch=branch, description="Cold drinks")
    
    item_chicken = MenuItem.objects.create(
        category=cat_mains, name="Grilled Chicken", price=Decimal("15.99"),
        description="Juicy grilled chicken breast with sides", is_active=True
    )
    # Link recipe to menu item
    recipe_chicken = Recipe.objects.create(
        menu_item=item_chicken,
    )
    RecipeItem.objects.create(recipe=recipe_chicken, inventory_item=inv_chicken, quantity=Decimal("0.3"), unit="kg")
    RecipeItem.objects.create(recipe=recipe_chicken, inventory_item=inv_tomato, quantity=Decimal("0.1"), unit="kg")
    
    item_pasta = MenuItem.objects.create(
        category=cat_mains, name="Tomato Pasta", price=Decimal("12.99"),
        description="Fresh pasta with tomato sauce", is_active=True
    )
    recipe_pasta = Recipe.objects.create(
        menu_item=item_pasta,
    )
    RecipeItem.objects.create(recipe=recipe_pasta, inventory_item=inv_flour, quantity=Decimal("0.2"), unit="kg")
    RecipeItem.objects.create(recipe=recipe_pasta, inventory_item=inv_tomato, quantity=Decimal("0.2"), unit="kg")
    
    item_cola = MenuItem.objects.create(
        category=cat_drinks, name="Cola", price=Decimal("2.99"),
        description="Chilled cola", is_active=True
    )

    # 5. Cashier Shift & Orders (Generate 30 days of random data for dashboards)
    user, _ = User.objects.get_or_create(username="cashier_demo")
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    menu_items = [item_chicken, item_pasta, item_cola]
    now = timezone.now()
    
    for day_offset in range(30):
        shift_date = now - timedelta(days=(29 - day_offset))
        
        shift = CashierShift.objects.create(
            user=user, branch=branch, 
            opening_balance=Decimal("100.00")
        )
        # Fix the created_at/start_time for the shift
        CashierShift.objects.filter(pk=shift.pk).update(start_time=shift_date.replace(hour=8, minute=0))
        
        # 5 to 15 orders per day
        daily_sales = Decimal("0.00")
        for _ in range(random.randint(5, 15)):
            order = Order.objects.create(
                branch=branch,
                table=random.choice(tables),
                waiter=user,
                shift=shift
            )
            # Add 1 to 4 items
            order_total = Decimal("0.00")
            for _ in range(random.randint(1, 4)):
                m_item = random.choice(menu_items)
                qty = random.randint(1, 3)
                OrderItem.objects.create(
                    order=order, menu_item=m_item, quantity=qty,
                    price=m_item.price
                )
                order_total += (m_item.price * qty)
                
            order.total_amount = order_total
            order.save()
            # Fake the created_at to be in the past
            Order.objects.filter(pk=order.pk).update(created_at=shift_date.replace(hour=random.randint(9, 22), minute=random.randint(0, 59)))
            
            daily_sales += order_total
            
        shift.closing_balance = shift.opening_balance + daily_sales
        shift.is_open = False
        shift.save()
        CashierShift.objects.filter(pk=shift.pk).update(end_time=shift_date.replace(hour=23, minute=0))

    print("Successfully seeded 30 days of data for dashboards and records.")

if __name__ == "__main__":
    seed()
