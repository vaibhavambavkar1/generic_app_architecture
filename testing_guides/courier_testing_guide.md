# Courier Module Testing Guide

## 1. Overview
This document outlines the testing procedures and critical paths for the **Courier** app within the Generic Logistics Management System (LMS). The Courier module handles Last-Mile Delivery, Waybill creation, pricing calculations based on volumetric weight, Dispatch Manifesting via HTMX dashboards, and automated Accounts Receivable (AR) integration.

## 2. Prerequisites & Setup
Before testing the Courier module, ensure the following foundational data is present in the local database:

- **Customer:** At least one active Customer (`crm.models.Customer`).
- **Organization:** A valid Organization record to bypass the `OrganizationEnforcementMiddleware`.
- **Zones:** Origin and Destination Zones (`logistics_core.models.Zone`).
- **Service Type:** At least one ServiceType (e.g., "Express Delivery", `logistics_core.models.ServiceType`) to calculate Waybill pricing.
- **Vehicles:** Active Vehicles in the fleet (`fleet_mgmt.models.Vehicle`).
- **Drivers:** Employees assigned to Logistics department (`hrms.models.Employee`).
- **Financial Accounts:** 
  - AR Account: Code `1100` (Category: ASSET)
  - Freight Revenue Account: Code `4000` (Category: REVENUE)

If running automated tests, append the `--noinput` flag when executing tests in Docker to bypass the test database deletion prompt:
```bash
docker exec erp_framework_web_dev python manage.py test courier --noinput
```

## 3. Core Functionality to Test

### 3.1. Waybill Pricing & Volumetric Calculation
- **Scenario:** Create a new Waybill with both physical weight (e.g., 10kg) and volume (e.g., 0.10 m³).
- **Expected Outcome:** 
  - The system calculates volumetric weight using the formula: `volume_m3 * 200`. (e.g., 0.10 * 200 = 20kg).
  - The `chargeable_weight` field must automatically select the greater of the physical weight and the volumetric weight.
  - The `price` must be calculated dynamically based on the associated `ServiceType` base rate and per-kg rate.

### 3.2. Finite State Machine (FSM) Transitions
- **Scenario:** Trace a Waybill through its lifecycle.
- **Valid Transitions:**
  - `Draft` ➔ `Manifested` (Upon addition to a Dispatch Manifest).
  - `Manifested` ➔ `In Transit` (When the Manifest is dispatched).
  - `In Transit` ➔ `Out for Delivery` ➔ `Delivered`.
- **Expected Outcome:** FSM guards should prevent invalid state jumps (e.g., a Waybill cannot go directly from `Draft` to `Delivered`).

### 3.3. HTMX Dispatcher Dashboard (UI Testing)
- **Scenario:** Navigate to the Dispatcher Dashboard (`/courier/dashboard/`).
- **Test Steps:**
  1. Create an empty Dispatch Manifest in `Draft` status.
  2. Use the barcode scanner input to type a Waybill Number that is currently in `Draft` state.
  3. Hit "Enter".
- **Expected Outcome:** 
  - The HTMX request should add the Waybill to the `ManifestItem` table without a full page reload.
  - The Waybill state must update to `Manifested`.
  - Scanning a Waybill that is already `In Transit` should return an inline error toast/message.

### 3.4. Financial Ledger Integration (Signals)
- **Scenario:** Deliver a Waybill to trigger revenue recognition.
- **Test Steps:** Move a Waybill's state from `Out for Delivery` to `Delivered`.
- **Expected Outcome:** 
  - The `post_save` signal `generate_waybill_invoice` (in `logistics_finance.signals`) must intercept this state change.
  - An atomic `JournalEntry` should be created.
  - `JournalEntryLine` records should reflect a Debit to AR (1100) and a Credit to Revenue (4000) for the exact amount of the Waybill `price`.

### 3.5. PDF Generation via ReportLab
- **Scenario:** Click the "Download PDF" button or hit the endpoint `/courier/waybill/<id>/pdf/`.
- **Expected Outcome:** Returns a well-formatted PDF file using `django.http.FileResponse`, showing barcodes, pricing, and origin/destination data.

## 4. Known Edge Cases to Verify
- **Missing Service Type:** Ensure Waybills default to a price of `0.00` and do not break the UI if a ServiceType is not provided.
- **Empty Scanner Inputs:** Verify that submitting a blank HTMX form does not create an empty `ManifestItem` or crash the backend.
- **Database Initialization:** Ensure `django.core.exceptions.ValidationError` is avoided in unit tests by fully populating `Organization` fields (e.g., `owner_name`, `email`).
