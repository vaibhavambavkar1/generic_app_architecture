from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from django.contrib.auth import get_user_model
from freight.models import FreightBooking, BillOfLading, AirWaybill, CustomsDeclaration, FreightLeg
from crm.models import Customer
from logistics_core.models import Location, ServiceType
from inventory.models import Supplier
from core.models import Organization

User = get_user_model()

class FreightManagementTests(TestCase):
    def setUp(self):
        # Base Requirements
        Organization.objects.create(name='Test Org', owner_name='Owner', email='test@org.com')
        
        self.user = User.objects.create_user(username='testfreight', password='password123')
        self.client = Client()
        self.client.force_login(self.user)
        
        # Test Data
        self.shipper = Customer.objects.create(name="Shipper Inc")
        self.consignee = Customer.objects.create(name="Consignee Ltd")
        
        self.port_a = Location.objects.create(name="Port of Shanghai", code="SHA")
        self.port_b = Location.objects.create(name="Port of Los Angeles", code="LAX")
        
        self.carrier = Supplier.objects.create(name="Maersk Line")
        self.service = ServiceType.objects.create(name="Ocean Freight FCL")
        
        # Booking
        self.booking = FreightBooking.objects.create(
            booking_number="FRT-2026-001",
            shipper=self.shipper,
            consignee=self.consignee,
            origin_port=self.port_a,
            destination_port=self.port_b,
            service_type=self.service,
            weight_kg=Decimal("15000.00"),
            volume_m3=Decimal("30.00"),
            status='Draft'
        )

    def test_booking_creation(self):
        """Test the FreightBooking model creation."""
        self.assertEqual(self.booking.booking_number, "FRT-2026-001")
        self.assertEqual(str(self.booking), "Freight FRT-2026-001")
        self.assertEqual(self.booking.shipper, self.shipper)

    def test_freight_fsm_transitions(self):
        """Test FSM transitions for the FreightBooking lifecycle."""
        # Draft -> Quoted -> Booked -> Received -> Loaded -> In Transit -> Arrived -> Cleared -> Delivered
        self.booking.quote()
        self.booking.save()
        self.assertEqual(self.booking.status, 'Quoted')
        
        self.booking.book()
        self.booking.save()
        self.assertEqual(self.booking.status, 'Booked')
        
        self.booking.receive()
        self.booking.save()
        self.assertEqual(self.booking.status, 'Received')
        
        self.booking.load()
        self.booking.save()
        self.assertEqual(self.booking.status, 'Loaded')

        self.booking.transit()
        self.booking.save()
        self.assertEqual(self.booking.status, 'In Transit')
        
        self.booking.arrive()
        self.booking.save()
        self.assertEqual(self.booking.status, 'Arrived')
        
        self.booking.clear_customs()
        self.booking.save()
        self.assertEqual(self.booking.status, 'Cleared')
        
        self.booking.deliver()
        self.booking.save()
        self.assertEqual(self.booking.status, 'Delivered')

    def test_customs_fsm(self):
        """Test Customs Declaration FSM."""
        customs = CustomsDeclaration.objects.create(
            booking=self.booking,
            declaration_number="CUST-999",
            duty_amount=Decimal("1500.00"),
            status='Draft'
        )
        customs.submit()
        customs.save()
        self.assertEqual(customs.status, 'Submitted')
        
        customs.clear()
        customs.save()
        self.assertEqual(customs.status, 'Cleared')

    def test_related_documents(self):
        """Test that BOL, AWB, and Legs correctly attach to a booking."""
        bol = BillOfLading.objects.create(
            booking=self.booking,
            bol_number="BOL-OCEAN-1",
            vessel_name="MSC Oscar",
            voyage_number="V123"
        )
        awb = AirWaybill.objects.create(
            booking=self.booking, # Note: realistically a booking has one or the other
            awb_number="AWB-AIR-1",
            flight_number="CX880"
        )
        leg1 = FreightLeg.objects.create(
            booking=self.booking,
            sequence=1,
            origin=self.port_a,
            destination=self.port_b,
            carrier=self.carrier,
            mode_of_transport='SEA'
        )
        
        self.assertEqual(self.booking.bol, bol)
        self.assertEqual(self.booking.awb, awb)
        self.assertEqual(self.booking.legs.count(), 1)
        self.assertEqual(self.booking.legs.first(), leg1)

    def test_freight_tracking_view(self):
        """Test the freight tracking dashboard view renders properly."""
        # Need to create BOL/AWB to test the template contexts
        BillOfLading.objects.create(
            booking=self.booking, bol_number="TEST", vessel_name="Vessel", voyage_number="1"
        )
        CustomsDeclaration.objects.create(
            booking=self.booking, declaration_number="CUST", duty_amount=Decimal('0')
        )
        FreightLeg.objects.create(
            booking=self.booking, sequence=1, origin=self.port_a, destination=self.port_b, mode_of_transport='SEA'
        )

        url = reverse('freight:tracking', args=[self.booking.booking_number])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'freight/tracking_dashboard.html')
        self.assertContains(response, self.booking.booking_number)
        self.assertTrue(response.context['has_bol'])
        self.assertFalse(response.context['has_awb'])
        self.assertTrue(response.context['has_customs'])
        self.assertEqual(len(response.context['legs']), 1)
