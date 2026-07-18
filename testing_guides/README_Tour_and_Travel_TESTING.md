# Tour & Travel Packages — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic Booking Management System when configured for **Tour & Travel Packages**.

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
   - **Preset**: Select `Tour & Travel Packages` from the dropdown list.
   - **Business Name**: Enter a name (e.g., "Test Tour & Travel Packages Business").
   - **Timezone**: Set to your local timezone.
   - **Currency**: `USD` or your local currency.
   - Click **Complete Setup** to initialize the multi-tenant profile.

---

## Phase 2: Resource Configuration

1. **Create a Resource Type (Package)**
   - Navigate to **Resources** > **Add Resource Type** (via [http://localhost:8000/admin/bookings/resourcetype/add/](http://localhost:8000/admin/bookings/resourcetype/add/)).
   - **Name**: `3-Day Mountain Trek`
   - **Default Capacity**: `1`
   - **Default Slot Duration**: `60` (Minutes) if applicable.

2. **Create the Resource**
   - Navigate to **Resources** > **Add Resource** (via [http://localhost:8000/admin/bookings/resource/add/](http://localhost:8000/admin/bookings/resource/add/)).
   - **Name**: `3-Day Mountain Trek 01`
   - **Code**: `RES-01`
   - **Resource Type**: `3-Day Mountain Trek`

---

## Phase 3: Scheduling & Pricing

1. **Set Operating Schedule**
   - Navigate to **Schedules** > **Add Schedule** (via [http://localhost:8000/bookings/schedules/](http://localhost:8000/bookings/schedules/)).
   - **Resource**: `3-Day Mountain Trek 01`
   - **Day of Week**: Select an upcoming day.
   - **Start Time**: `09:00:00`
   - **End Time**: `18:00:00`

2. **Set Pricing**
   - Navigate to **Pricing Rules** (via [http://localhost:8000/admin/bookings/pricingrule/add/](http://localhost:8000/admin/bookings/pricingrule/add/)).
   - **Resource Type**: `3-Day Mountain Trek`
   - **Pricing Model**: `FLAT`
   - **Base Price**: `300.00`
   - **Valid From**: Today's Date

---

## Phase 4: Customer Experience (Public Portal)

1. **Open the Customer Portal**
   - Open a new Incognito browser window and navigate to the public widget: [http://localhost:8000/bookings/book/](http://localhost:8000/bookings/book/)

2. **Book the Service**
   - **Select Resource**: Choose `3-Day Mountain Trek 01`.
   - **Pick a Date**: Select the date you configured in the schedule.
   - **Select Slot**: Depending on the mode (`date_range`), pick your specific slot, duration, or seat selection.
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
