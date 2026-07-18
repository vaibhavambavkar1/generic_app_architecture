import os

industries = [
    ("Hotel_and_Resort", "Hotel & Resort Bookings", "date_range", "Room Type", "Deluxe Suite", "DAILY", "150.00"),
    ("Salon_and_Spa", "Salon & Spa", "time_slot", "Service", "Haircut & Styling", "FLAT", "40.00"),
    ("Gym_and_Fitness", "Gym & Fitness Classes", "time_slot", "Class", "Yoga Session", "FLAT", "15.00"),
    ("Sports_Ground", "Sports Ground Booking", "time_slot", "Court", "Tennis Court 1", "HOURLY", "25.00"),
    ("Banquet_Hall", "Banquet Hall Booking", "date_range", "Hall", "Grand Ballroom", "DAILY", "1500.00"),
    ("Marriage_Hall", "Marriage Hall Booking", "date_range", "Hall", "Royal Wedding Hall", "DAILY", "2500.00"),
    ("Conference_Room", "Conference Room Booking", "time_slot", "Room", "Boardroom A", "HOURLY", "50.00"),
    ("Coworking_Space", "Coworking Spaces", "date_range", "Desk Type", "Hot Desk", "DAILY", "20.00"),
    ("Vehicle_Rental", "Vehicle Rental", "date_range", "Vehicle Class", "SUV - Toyota RAV4", "DAILY", "60.00"),
    ("Taxi_Booking", "Taxi Booking", "time_slot", "Vehicle", "Premium Sedan", "FLAT", "30.00"),
    ("Tour_and_Travel", "Tour & Travel Packages", "date_range", "Package", "3-Day Mountain Trek", "FLAT", "300.00"),
    ("Event_Ticket", "Event Ticket Booking", "seat_selection", "Section", "VIP Front Row", "FLAT", "100.00"),
    ("Cinema_Booking", "Cinema Booking", "seat_selection", "Screen", "IMAX Screen 1", "FLAT", "18.00"),
    ("Bus_Booking", "Bus Booking", "seat_selection", "Route", "NY to Boston - Express", "FLAT", "35.00"),
    ("Training_Institute", "Training Institute Batch Booking", "time_slot", "Batch", "Python Bootcamp Q3", "FLAT", "500.00"),
    ("Consultant_Appointment", "Consultant Appointment Booking", "time_slot", "Consultant", "Jane Doe - Legal", "HOURLY", "150.00"),
    ("Home_Service", "Home Service Booking", "time_slot", "Service", "AC Repair & Servicing", "FLAT", "80.00"),
    ("Equipment_Rental", "Equipment Rental", "date_range", "Equipment", "Heavy Excavator", "DAILY", "400.00"),
    ("Photography", "Photography Booking", "time_slot", "Package", "Wedding Shoot Full Day", "FLAT", "1200.00"),
    ("Restaurant_Table", "Restaurant Table Reservation", "time_slot", "Table Type", "Window Table for 2", "FLAT", "0.00"),
    ("Parking_Slot", "Parking Slot Booking", "time_slot", "Zone", "Premium Covered Parking", "HOURLY", "5.00"),
    ("Warehouse_Slot", "Warehouse Slot Booking", "date_range", "Storage Unit", "Climate Controlled 10x10", "DAILY", "15.00"),
    ("Cargo_Appointment", "Cargo Appointment Booking", "time_slot", "Dock", "Loading Dock 4", "HOURLY", "25.00"),
    ("Interview_Slot", "Interview Slot Booking", "time_slot", "Panel", "Software Engineer Panel", "FLAT", "0.00"),
    ("Government_Appointment", "Government Appointment Booking", "time_slot", "Service", "Passport Renewal", "FLAT", "0.00"),
]

template = """# {name} — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic Booking Management System when configured for **{name}**.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

---

## Phase 1: Business Setup (Tenant Initialization)

1. **Access the Setup Wizard**
   - Navigate to: [http://localhost:8000/bookings/setup/](http://localhost:8000/bookings/setup/)
   - Log in using your Django Admin credentials if prompted.

2. **Configure the Industry Preset**
   - **Preset**: Select `{name}` from the dropdown list.
   - **Business Name**: Enter a name (e.g., "Test {name} Business").
   - **Timezone**: Set to your local timezone.
   - **Currency**: `USD` or your local currency.
   - Click **Complete Setup** to initialize the multi-tenant profile.

---

## Phase 2: Resource Configuration

1. **Create a Resource Type ({resource_type_name})**
   - Navigate to **Resources** > **Add Resource Type** (via [http://localhost:8000/admin/bookings/resourcetype/add/](http://localhost:8000/admin/bookings/resourcetype/add/)).
   - **Name**: `{resource_name}`
   - **Default Capacity**: `1`
   - **Default Slot Duration**: `60` (Minutes) if applicable.

2. **Create the Resource**
   - Navigate to **Resources** > **Add Resource** (via [http://localhost:8000/admin/bookings/resource/add/](http://localhost:8000/admin/bookings/resource/add/)).
   - **Name**: `{resource_name} 01`
   - **Code**: `RES-01`
   - **Resource Type**: `{resource_name}`

---

## Phase 3: Scheduling & Pricing

1. **Set Operating Schedule**
   - Navigate to **Schedules** > **Add Schedule** (via [http://localhost:8000/bookings/schedules/](http://localhost:8000/bookings/schedules/)).
   - **Resource**: `{resource_name} 01`
   - **Day of Week**: Select an upcoming day.
   - **Start Time**: `09:00:00`
   - **End Time**: `18:00:00`

2. **Set Pricing**
   - Navigate to **Pricing Rules** (via [http://localhost:8000/admin/bookings/pricingrule/add/](http://localhost:8000/admin/bookings/pricingrule/add/)).
   - **Resource Type**: `{resource_name}`
   - **Pricing Model**: `{pricing_model}`
   - **Base Price**: `{base_price}`
   - **Valid From**: Today's Date

---

## Phase 4: Customer Experience (Public Portal)

1. **Open the Customer Portal**
   - Open a new Incognito browser window and navigate to the public widget: [http://localhost:8000/bookings/book/](http://localhost:8000/bookings/book/)

2. **Book the Service**
   - **Select Resource**: Choose `{resource_name} 01`.
   - **Pick a Date**: Select the date you configured in the schedule.
   - **Select Slot**: Depending on the mode (`{mode}`), pick your specific slot, duration, or seat selection.
   - **Checkout**: Fill in dummy customer details and submit.

---

## Phase 5: Admin Workflow & Reports

1. **Manage the Booking**
   - Return to your Admin Dashboard: [http://localhost:8000/bookings/](http://localhost:8000/bookings/)
   - Locate the newly created booking.
   - Process the workflow state transitions (e.g., Pending -> Confirmed -> Completed).
   - Generate the PDF receipt/invoice.

2. **View Analytics**
   - Navigate to the **Reports** tab: [http://localhost:8000/bookings/reports/](http://localhost:8000/bookings/reports/)
   - Verify that the revenue and booking counts accurately reflect your test data.
"""

for slug, name, mode, resource_type_name, resource_name, pricing_model, base_price in industries:
    filename = f"docs/testing_guides/README_{slug}_TESTING.md"
    content = template.format(
        name=name,
        mode=mode,
        resource_type_name=resource_type_name,
        resource_name=resource_name,
        pricing_model=pricing_model,
        base_price=base_price
    )
    with open(filename, "w") as f:
        f.write(content)

print(f"Generated {len(industries)} testing guides in docs/testing_guides/")
