from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from fleet_mgmt.models import Vehicle, Container, MaintenanceLog, DriverAssignment
from hrms.models import Employee
from core.models import Organization

User = get_user_model()

class FleetManagementTests(TestCase):
    def setUp(self):
        # Organization is required by middleware/models
        Organization.objects.create(
            name='Test Org',
            owner_name='Test Owner',
            email='test@example.com'
        )

        # Create a User and Employee for Driver Assignment
        self.user = User.objects.create_user(
            username='driver1', 
            email='driver1@example.com', 
            password='testpassword'
        )
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id="EMP-DRV-001",
            department="Logistics"
        )
        
        # Create a Vehicle
        self.vehicle = Vehicle.objects.create(
            registration_number="XYZ-1234",
            vehicle_type="TRUCK",
            make="Volvo",
            model="FH16",
            capacity_kg=Decimal('20000.00'),
            volume_m3=Decimal('50.00'),
            status='Available'
        )
        
        # Create a Container
        self.container = Container.objects.create(
            container_number="MSCU1234567",
            container_type="TEU",
            is_active=True
        )

    def test_vehicle_creation(self):
        """Test the Vehicle model creation and string representation."""
        self.assertEqual(self.vehicle.registration_number, "XYZ-1234")
        self.assertEqual(self.vehicle.capacity_kg, Decimal('20000.00'))
        self.assertEqual(str(self.vehicle), "XYZ-1234 (Truck (FTL))")

    def test_container_creation(self):
        """Test the Container model creation and string representation."""
        self.assertEqual(self.container.container_number, "MSCU1234567")
        self.assertEqual(str(self.container), "MSCU1234567 - 20ft Container (TEU)")

    def test_vehicle_fsm_transitions(self):
        """Test FSM state transitions for Vehicle."""
        # Initial state
        self.assertEqual(self.vehicle.status, 'Available')
        
        # Available -> Dispatched
        self.vehicle.dispatch()
        self.vehicle.save()
        self.assertEqual(self.vehicle.status, 'Dispatched')
        
        # Dispatched -> In Maintenance
        self.vehicle.send_to_maintenance()
        self.vehicle.save()
        self.assertEqual(self.vehicle.status, 'In Maintenance')
        
        # In Maintenance -> Available
        self.vehicle.mark_available()
        self.vehicle.save()
        self.assertEqual(self.vehicle.status, 'Available')
        
        # Available -> Out of Service
        self.vehicle.decommission()
        self.vehicle.save()
        self.assertEqual(self.vehicle.status, 'Out of Service')

    def test_driver_assignment(self):
        """Test that assigning a driver to a vehicle works as expected."""
        assignment = DriverAssignment.objects.create(
            vehicle=self.vehicle,
            driver=self.employee,
            assigned_from=timezone.now(),
            is_active=True
        )
        self.assertEqual(assignment.vehicle, self.vehicle)
        self.assertEqual(assignment.driver, self.employee)
        self.assertTrue(assignment.is_active)
        self.assertIn(self.employee.user.get_full_name(), str(assignment))

    def test_maintenance_log_creation(self):
        """Test the creation of maintenance logs for vehicles."""
        log = MaintenanceLog.objects.create(
            vehicle=self.vehicle,
            description="Oil change and brake replacement",
            cost=Decimal('450.00'),
            performed_by="Internal Workshop"
        )
        self.assertEqual(log.cost, Decimal('450.00'))
        self.assertEqual(log.vehicle, self.vehicle)
        self.assertTrue(str(log).startswith("Maintenance XYZ-1234 on"))
