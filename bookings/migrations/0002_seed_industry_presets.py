from django.db import migrations

def seed_presets(apps, schema_editor):
    IndustryPreset = apps.get_model('bookings', 'IndustryPreset')
    
    presets = [
        {
            "name": "Hotel & Resort",
            "slug": "hotel-resort",
            "icon": "hotel",
            "config": {
                "resource_label": "Room",
                "resource_label_plural": "Rooms",
                "booking_label": "Reservation",
                "customer_label": "Guest",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": True,
                "pricing_model": "PER_NIGHT",
                "cancellation_hours": 24,
                "max_advance_days": 365,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled", "NoShow"],
                "custom_fields": [
                    {"name": "guests_count", "type": "int", "required": True},
                    {"name": "room_service_pref", "type": "str", "required": False}
                ]
            }
        },
        {
            "name": "Hospital OPD",
            "slug": "hospital-opd",
            "icon": "hospital",
            "config": {
                "resource_label": "Doctor",
                "resource_label_plural": "Doctors",
                "booking_label": "Appointment",
                "customer_label": "Patient",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 15,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 2,
                "max_advance_days": 30,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled", "NoShow"],
                "custom_fields": [
                    {"name": "symptoms", "type": "str", "required": False},
                    {"name": "age", "type": "int", "required": True}
                ]
            }
        },
        {
            "name": "Salon & Spa",
            "slug": "salon-spa",
            "icon": "cut",
            "config": {
                "resource_label": "Stylist/Station",
                "resource_label_plural": "Stylists/Stations",
                "booking_label": "Appointment",
                "customer_label": "Client",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 45,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 4,
                "max_advance_days": 60,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled", "NoShow"]
            }
        },
        {
            "name": "Gym & Fitness",
            "slug": "gym-fitness",
            "icon": "dumbbell",
            "config": {
                "resource_label": "Class/Trainer",
                "resource_label_plural": "Classes/Trainers",
                "booking_label": "Class Booking",
                "customer_label": "Member",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 60,
                "allow_multiple_resources": False,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 12,
                "max_advance_days": 14,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "Completed", "Cancelled", "NoShow"]
            }
        },
        {
            "name": "Sports Ground",
            "slug": "sports-ground",
            "icon": "futbol",
            "config": {
                "resource_label": "Court/Ground",
                "resource_label_plural": "Courts/Grounds",
                "booking_label": "Slot Reservation",
                "customer_label": "Player",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 60,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "HOURLY",
                "cancellation_hours": 24,
                "max_advance_days": 30,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Banquet Hall",
            "slug": "banquet-hall",
            "icon": "glass-cheers",
            "config": {
                "resource_label": "Hall",
                "resource_label_plural": "Halls",
                "booking_label": "Event Reservation",
                "customer_label": "Host",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": False,
                "requires_capacity": True,
                "has_check_in_out": True,
                "pricing_model": "DAILY",
                "cancellation_hours": 72,
                "max_advance_days": 365,
                "requires_approval": True,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Marriage Hall",
            "slug": "marriage-hall",
            "icon": "ring",
            "config": {
                "resource_label": "Hall",
                "resource_label_plural": "Halls",
                "booking_label": "Wedding Reservation",
                "customer_label": "Client",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": False,
                "requires_capacity": True,
                "has_check_in_out": True,
                "pricing_model": "DAILY",
                "cancellation_hours": 168,
                "max_advance_days": 730,
                "requires_approval": True,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Conference Room",
            "slug": "conference-room",
            "icon": "users",
            "config": {
                "resource_label": "Meeting Room",
                "resource_label_plural": "Meeting Rooms",
                "booking_label": "Room Booking",
                "customer_label": "Organizer",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 30,
                "allow_multiple_resources": False,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "HOURLY",
                "cancellation_hours": 2,
                "max_advance_days": 30,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Coworking Space",
            "slug": "coworking-space",
            "icon": "laptop-house",
            "config": {
                "resource_label": "Desk/Cabin",
                "resource_label_plural": "Desks/Cabins",
                "booking_label": "Desk Pass",
                "customer_label": "Member",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "DAILY",
                "cancellation_hours": 24,
                "max_advance_days": 90,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Vehicle Rental",
            "slug": "vehicle-rental",
            "icon": "car",
            "config": {
                "resource_label": "Vehicle",
                "resource_label_plural": "Vehicles",
                "booking_label": "Rental Booking",
                "customer_label": "Renter",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": True,
                "pricing_model": "DAILY",
                "cancellation_hours": 24,
                "max_advance_days": 180,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Taxi Booking",
            "slug": "taxi-booking",
            "icon": "taxi",
            "config": {
                "resource_label": "Driver/Taxi",
                "resource_label_plural": "Drivers/Taxis",
                "booking_label": "Ride Booking",
                "customer_label": "Rider",
                "slot_mode": "time_slot",
                "slot_duration_minutes": None,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": True,
                "pricing_model": "FLAT",
                "cancellation_hours": 1,
                "max_advance_days": 7,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Tour & Travel",
            "slug": "tour-travel",
            "icon": "plane",
            "config": {
                "resource_label": "Tour Package",
                "resource_label_plural": "Tour Packages",
                "booking_label": "Tour Booking",
                "customer_label": "Traveler",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "PER_HEAD",
                "cancellation_hours": 72,
                "max_advance_days": 365,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Event Ticket",
            "slug": "event-ticket",
            "icon": "ticket-alt",
            "config": {
                "resource_label": "Seat/Zone",
                "resource_label_plural": "Seats/Zones",
                "booking_label": "Ticket Purchase",
                "customer_label": "Attendee",
                "slot_mode": "time_slot",
                "slot_duration_minutes": None,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 48,
                "max_advance_days": 180,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Cinema Booking",
            "slug": "cinema-booking",
            "icon": "film",
            "config": {
                "resource_label": "Seat",
                "resource_label_plural": "Seats",
                "booking_label": "Seat Booking",
                "customer_label": "Viewer",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 150,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 4,
                "max_advance_days": 7,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Bus Booking",
            "slug": "bus-booking",
            "icon": "bus",
            "config": {
                "resource_label": "Seat",
                "resource_label_plural": "Seats",
                "booking_label": "Seat Booking",
                "customer_label": "Passenger",
                "slot_mode": "time_slot",
                "slot_duration_minutes": None,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 12,
                "max_advance_days": 30,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Training Institute",
            "slug": "training-institute",
            "icon": "graduation-cap",
            "config": {
                "resource_label": "Batch/Class",
                "resource_label_plural": "Batches/Classes",
                "booking_label": "Enrollment",
                "customer_label": "Student",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": False,
                "requires_capacity": True,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 168,
                "max_advance_days": 90,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Consultant Appointment",
            "slug": "consultant-appointment",
            "icon": "user-tie",
            "config": {
                "resource_label": "Consultant",
                "resource_label_plural": "Consultants",
                "booking_label": "Consultation",
                "customer_label": "Client",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 30,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 24,
                "max_advance_days": 60,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled", "NoShow"]
            }
        },
        {
            "name": "Home Service",
            "slug": "home-service",
            "icon": "tools",
            "config": {
                "resource_label": "Technician",
                "resource_label_plural": "Technicians",
                "booking_label": "Job Booking",
                "customer_label": "Homeowner",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 120,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 4,
                "max_advance_days": 14,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Equipment Rental",
            "slug": "equipment-rental",
            "icon": "toolbox",
            "config": {
                "resource_label": "Equipment",
                "resource_label_plural": "Equipment",
                "booking_label": "Rental Booking",
                "customer_label": "Lessee",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": True,
                "pricing_model": "DAILY",
                "cancellation_hours": 24,
                "max_advance_days": 90,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Photography Booking",
            "slug": "photography-booking",
            "icon": "camera",
            "config": {
                "resource_label": "Photographer/Studio",
                "resource_label_plural": "Photographers/Studios",
                "booking_label": "Shoot Booking",
                "customer_label": "Client",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 60,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "HOURLY",
                "cancellation_hours": 48,
                "max_advance_days": 180,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Restaurant Table",
            "slug": "restaurant-table",
            "icon": "utensils",
            "config": {
                "resource_label": "Table",
                "resource_label_plural": "Tables",
                "booking_label": "Table Reservation",
                "customer_label": "Diner",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 120,
                "allow_multiple_resources": False,
                "requires_capacity": True,
                "has_check_in_out": True,
                "pricing_model": "FLAT",
                "cancellation_hours": 2,
                "max_advance_days": 30,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "CheckedIn", "Completed", "Cancelled", "NoShow"]
            }
        },
        {
            "name": "Parking Slot",
            "slug": "parking-slot",
            "icon": "parking",
            "config": {
                "resource_label": "Parking Space",
                "resource_label_plural": "Parking Spaces",
                "booking_label": "Parking Booking",
                "customer_label": "Driver",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 60,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": True,
                "pricing_model": "HOURLY",
                "cancellation_hours": 1,
                "max_advance_days": 7,
                "requires_approval": False,
                "workflow_states": ["Confirmed", "CheckedIn", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Warehouse Slot",
            "slug": "warehouse-slot",
            "icon": "warehouse",
            "config": {
                "resource_label": "Storage Bay",
                "resource_label_plural": "Storage Bays",
                "booking_label": "Storage Booking",
                "customer_label": "Depositor",
                "slot_mode": "date_range",
                "slot_duration_minutes": None,
                "allow_multiple_resources": True,
                "requires_capacity": True,
                "has_check_in_out": True,
                "pricing_model": "DAILY",
                "cancellation_hours": 72,
                "max_advance_days": 180,
                "requires_approval": True,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Cargo Appointment",
            "slug": "cargo-appointment",
            "icon": "shipping-fast",
            "config": {
                "resource_label": "Loading Dock",
                "resource_label_plural": "Loading Docks",
                "booking_label": "Dock Appointment",
                "customer_label": "Carrier",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 60,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": True,
                "pricing_model": "FLAT",
                "cancellation_hours": 12,
                "max_advance_days": 14,
                "requires_approval": True,
                "workflow_states": ["Pending", "Confirmed", "CheckedIn", "Completed", "Cancelled"]
            }
        },
        {
            "name": "Interview Slot",
            "slug": "interview-slot",
            "icon": "briefcase",
            "config": {
                "resource_label": "Room/Link",
                "resource_label_plural": "Rooms/Links",
                "booking_label": "Interview slot",
                "customer_label": "Candidate",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 45,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 24,
                "max_advance_days": 30,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled", "NoShow"]
            }
        },
        {
            "name": "Government Appointment",
            "slug": "government-appointment",
            "icon": "university",
            "config": {
                "resource_label": "Counter/Officer",
                "resource_label_plural": "Counters/Officers",
                "booking_label": "Appointment Slot",
                "customer_label": "Citizen",
                "slot_mode": "time_slot",
                "slot_duration_minutes": 20,
                "allow_multiple_resources": False,
                "requires_capacity": False,
                "has_check_in_out": False,
                "pricing_model": "FLAT",
                "cancellation_hours": 24,
                "max_advance_days": 60,
                "requires_approval": False,
                "workflow_states": ["Pending", "Confirmed", "Completed", "Cancelled", "NoShow"]
            }
        }
    ]
    
    for preset in presets:
        IndustryPreset.objects.get_or_create(
            name=preset['name'],
            defaults={
                'slug': preset['slug'],
                'icon': preset['icon'],
                'config': preset['config']
            }
        )

def remove_presets(apps, schema_editor):
    IndustryPreset = apps.get_model('bookings', 'IndustryPreset')
    IndustryPreset.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_presets, remove_presets),
    ]
