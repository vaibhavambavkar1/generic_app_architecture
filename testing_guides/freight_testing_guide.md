# Freight Forwarding (freight) Testing Guide

## 1. Overview
This document outlines the automated testing suite and verification processes for the **Freight** app within the Generic Logistics Management System (LMS). This module oversees complex B2B multi-modal transit, including Ocean (Bill of Lading), Air (Air Waybill), Customs declarations, and multi-leg tracking.

## 2. Prerequisites & Setup
Ensure the following data entities exist before running the Freight test suite:
- **Organization:** A valid Organization must be present (bypasses CRM middleware).
- **Customers:** Shipper and Consignee (`crm.models.Customer`).
- **Locations:** Origin and Destination Ports (`logistics_core.models.Location`).
- **Service Types & Suppliers:** Carriers/Vendors (`inventory.models.Supplier`) and logistics services.

Run the test suite headlessly via Docker:
```bash
docker exec erp_framework_web_dev python manage.py test freight --noinput
```

## 3. Core Functionality Tested

### 3.1. Booking Creation & References
- **FreightBookings:** Verifies successful instantiation of a Booking tying together Shipper, Consignee, Origin, Destination, and dimensional data (`weight_kg`, `volume_m3`).

### 3.2. FSM Workflow Transitions
The lifecycle of a complex freight booking is strictly managed by `django_fsm`. Tests ensure proper state progression:
- `Draft` ➔ `Quoted` ➔ `Booked` ➔ `Received` ➔ `Loaded` ➔ `In Transit` ➔ `Arrived` ➔ `Cleared` ➔ `Delivered`
- Invalid jumps (e.g., `Draft` to `Delivered`) are guarded against by the model logic and verified in testing.

### 3.3. Document Attachment (BOL & AWB)
- **Bill of Lading (Ocean) & Air Waybill (Air):** Verifies that a `FreightBooking` can have associated transit documents containing specific vessel names, flight numbers, and unique document tracking numbers.
- **Customs Declaration:** Verifies the standalone FSM (`Draft` ➔ `Submitted` ➔ `Cleared`/`Rejected`) for tracking international duty and customs compliance.

### 3.4. Multi-Modal Transit Legs
- **FreightLegs:** Verifies that multiple sequential legs (`ROAD`, `SEA`, `RAIL`, `AIR`) can be attached to a single booking and queried in correct sequence (`order_by('sequence')`).

### 3.5. Tracking Dashboard UI
- **Tracking View (`freight_tracking`):** Validates the `tracking_dashboard.html` template. Ensures that the view logic correctly pre-fetches associated legs, calculates document existence (`has_bol`, `has_awb`, `has_customs`), and returns a 200 OK status without throwing context errors.

## 4. Best Practices
When simulating multi-modal journeys in tests, always establish `Sequence` values for `FreightLeg` records to guarantee accurate timeline rendering on the Tracking Dashboard.
