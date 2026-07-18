# Hospital OPD Booking System — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic Booking Management System when configured as a **Hospital OPD (Outpatient Department) & Appointment System**.

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
   - **Preset**: Select `Hospital OPD & Appointment Bookings` from the dropdown list.
   - **Business Name**: Enter a name (e.g., "City General Hospital").
   - **Timezone**: Set to your local timezone.
   - **Currency**: `USD` or your local currency.
   - Click **Complete Setup** to initialize the multi-tenant profile.

---

## Phase 2: Resource Configuration (Adding Doctors)

1. **Create a Resource Type (Specialization)**
   - Navigate to **Resources** > **Add Resource Type** (via the Django Admin at [http://localhost:8000/admin/bookings/resourcetype/add/](http://localhost:8000/admin/bookings/resourcetype/add/)).
   - **Name**: `Cardiologist`
   - **Default Capacity**: `1` (One patient per slot)
   - **Default Slot Duration**: `15` (Minutes)

2. **Create the Doctor (Resource)**
   - Navigate to **Resources** > **Add Resource** (via the Django Admin at [http://localhost:8000/admin/bookings/resource/add/](http://localhost:8000/admin/bookings/resource/add/)).
   - **Name**: `Dr. Sarah Smith`
   - **Code**: `DOC-01`
   - **Resource Type**: `Cardiologist`

---

## Phase 3: Scheduling (Defining OPD Shifts)

1. **Set Shift Timings**
   - Navigate to **Schedules** > **Add Schedule** (via [http://localhost:8000/bookings/schedules/](http://localhost:8000/bookings/schedules/)).
   - **Resource**: `Dr. Sarah Smith`
   - **Day of Week**: `Monday` (or any upcoming day)
   - **Start Time**: `09:00:00`
   - **End Time**: `13:00:00` (1:00 PM)
   - **Slot Duration**: `15` minutes
   - *Note: The system's HTMX SlotEngine will dynamically cut this 4-hour window into 16 distinct 15-minute consultation slots.*

2. **Set Consultation Pricing**
   - Navigate to **Pricing Rules** (via [http://localhost:8000/admin/bookings/pricingrule/add/](http://localhost:8000/admin/bookings/pricingrule/add/)).
   - **Resource Type**: `Cardiologist`
   - **Pricing Model**: `FLAT`
   - **Base Price**: `50.00`
   - **Valid From**: Today's Date

---

## Phase 4: Patient Experience (Public Portal)

1. **Open the Customer Portal**
   - Open a new Incognito browser window and navigate to the public widget: [http://localhost:8000/bookings/book/](http://localhost:8000/bookings/book/)

2. **Book an Appointment**
   - **Select Resource**: Choose `Dr. Sarah Smith`.
   - **Pick a Date**: Select the upcoming Monday from the calendar.
   - **Select Slot**: You will see dynamically generated 15-minute intervals (e.g., 09:00, 09:15, 09:30). Click one.
   - **Checkout**: Fill in dummy patient details (Name, Email, Phone) and submit the form.

---

## Phase 5: Receptionist/Admin Workflow

1. **Manage the Booking**
   - Close the incognito window and return to your Admin Dashboard: [http://localhost:8000/bookings/](http://localhost:8000/bookings/)
   - Locate the newly created appointment in the **Pending** or **Confirmed** state.
   - Click into the booking details.

2. **State Transitions**
   - When the patient arrives, click the **Check-In** action button.
   - When the consultation concludes, click the **Mark Completed** action button.
   - *Observe how the `django-fsm` orchestrator prevents invalid workflow states (e.g., jumping from Pending directly to Completed).*

3. **Generate Documents**
   - Click the **Download PDF** button to stream the ReportLab-generated OPD consultation receipt.

---

## Phase 6: Analytics & Reporting

1. **View Live Metrics**
   - Navigate to the **Reports** tab: [http://localhost:8000/bookings/reports/](http://localhost:8000/bookings/reports/)
   - **Revenue Chart**: Observe the $50.00 revenue spike for today's date.
   - **Popularity Chart**: See `Dr. Sarah Smith` listed in the bar chart.
   - **Status Chart**: See the "Completed" slice represented in the pie chart.

---
*This configuration demonstrates how a single highly-abstracted booking application can seamlessly power a rigid scheduling structure like a medical OPD without modifying backend code.*
