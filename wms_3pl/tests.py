from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from core.models import Organization
from crm.models import Customer
from inventory.models import Warehouse
from generic_store_mgmt.models import Product, Category, UnitOfMeasure
from hrms.models import Employee
from wms_3pl.models import (
    WarehouseZone, Aisle, Rack, Bin, 
    ClientInventory, PutawayTask, PickList, PickListItem
)

User = get_user_model()

class WMS3PLTests(TestCase):
    def setUp(self):
        # 1. Base Setup
        Organization.objects.create(name='Test Org', owner_name='Owner', email='test@org.com')
        self.user = User.objects.create_user(username='wmsuser', password='password123')
        
        # 2. Master Data Setup
        self.customer = Customer.objects.create(name="3PL Client A")
        self.employee = Employee.objects.create(user=self.user, employee_id="WMS-001", department="Warehouse")
        self.category = Category.objects.create(name="Electronics")
        self.uom = UnitOfMeasure.objects.create(name="Piece", code="PCS")
        self.product = Product.objects.create(
            name="Gaming Monitor", 
            sku="MON-01", 
            category=self.category, 
            uom=self.uom,
            purchase_price=Decimal("200.00"),
            selling_price=Decimal("300.00")
        )
        
        # 3. Warehouse Topology Setup
        self.warehouse = Warehouse.objects.create(name="North Facility")
        self.zone = WarehouseZone.objects.create(warehouse=self.warehouse, name="Zone A", zone_type="STORAGE")
        self.aisle = Aisle.objects.create(zone=self.zone, code="A1")
        self.rack = Rack.objects.create(aisle=self.aisle, code="R1")
        self.bin = Bin.objects.create(rack=self.rack, code="B1", max_weight_kg=Decimal("100.00"), max_volume_m3=Decimal("5.00"))
        
        # 4. Putaway Task for Receiving
        self.putaway = PutawayTask.objects.create(
            task_number="PA-2026-001",
            client=self.customer,
            assigned_to=self.employee,
            product=self.product,
            quantity=50,
            target_bin=self.bin,
            status="Draft"
        )
        
        # 5. Picklist for Shipping
        self.picklist = PickList.objects.create(
            picklist_number="PL-2026-001",
            client=self.customer,
            assigned_to=self.employee,
            order_reference="SO-9999",
            status="Draft"
        )
        self.picklist_item = PickListItem.objects.create(
            picklist=self.picklist,
            product=self.product,
            source_bin=self.bin,
            quantity_to_pick=20
        )

    def test_warehouse_topology_creation(self):
        """Test proper creation and string formatting of the Warehouse Topology hierarchy."""
        self.assertEqual(str(self.zone), "North Facility - Zone A")
        self.assertEqual(str(self.aisle), "North Facility - Zone A - Aisle A1")
        self.assertEqual(str(self.rack), "North Facility - Zone A - Aisle A1 - Rack R1")
        self.assertEqual(str(self.bin), "North Facility - Zone A - Aisle A1 - Rack R1 - Bin B1")

    def test_putaway_task_fsm_and_inventory(self):
        """Test PutawayTask FSM transitions and verify it properly credits the ClientInventory upon completion."""
        # Check initial state
        self.assertEqual(self.putaway.status, "Draft")
        
        # Draft -> Assigned
        self.putaway.assign()
        self.putaway.save()
        self.assertEqual(self.putaway.status, "Assigned")
        
        # Assigned -> In Progress
        self.putaway.start_putaway()
        self.putaway.save()
        self.assertEqual(self.putaway.status, "In Progress")
        
        # In Progress -> Completed
        self.putaway.complete_putaway()
        self.putaway.save()
        self.assertEqual(self.putaway.status, "Completed")
        
        # Completing Putaway should have created ClientInventory for this bin
        inventory = ClientInventory.objects.get(
            client=self.customer, 
            product=self.product, 
            bin_location=self.bin
        )
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory.quantity, 50)
        self.assertIn("3PL Client A", str(inventory))
        self.assertIn("Gaming Monitor", str(inventory))

    def test_picklist_fsm_and_inventory_deduction(self):
        """Test Picklist FSM transitions and PickListItem marking deducted from ClientInventory."""
        # First, simulate stock existing in the bin
        ClientInventory.objects.create(
            client=self.customer,
            product=self.product,
            bin_location=self.bin,
            quantity=50
        )
        
        # Check FSM Picklist States
        self.picklist.assign()
        self.picklist.save()
        self.assertEqual(self.picklist.status, "Assigned")
        
        self.picklist.start_picking()
        self.picklist.save()
        self.assertEqual(self.picklist.status, "Picking")
        
        # Picker marks items as picked (should deduct from inventory)
        self.picklist_item.mark_picked(20)
        
        self.assertEqual(self.picklist_item.quantity_picked, 20)
        
        # Verify inventory was deducted from 50 -> 30
        inventory = ClientInventory.objects.get(
            client=self.customer, 
            product=self.product, 
            bin_location=self.bin
        )
        self.assertEqual(inventory.quantity, 30)
        
        # Finish the FSM
        self.picklist.pack()
        self.picklist.save()
        self.assertEqual(self.picklist.status, "Packed")
        
        self.picklist.ship()
        self.picklist.save()
        self.assertEqual(self.picklist.status, "Shipped")
