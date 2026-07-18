# Logistics Finance (`logistics_finance`) Testing Guide

## 1. Overview
This document outlines the testing suite for the **Logistics Finance** integration app. This module serves as the bridge between operational logistics events (e.g., freight delivery, 3PL storage) and the corporate double-entry accounting ledger via Django Signals.

## 2. Prerequisites & Setup
Because this module integrates deeply across multiple domains, its test setup requires initializing baseline data across several apps:
- **Finance:** Core Chart of Accounts including `1100` (Accounts Receivable), `2000` (Accounts Payable), `4000` (Revenue), and `5000` (Expense).
- **CRM / Vendors:** Both Customers (for AR) and Suppliers/Carriers (for AP).
- **Logistics Entities:** Waybills (`courier`), FreightBookings (`freight`), and PutawayTasks (`wms_3pl`).

To run the suite headlessly without interactive database deletion prompts:
```bash
docker exec erp_framework_web_dev python manage.py test logistics_finance --noinput
```

## 3. Core Functionality Tested

### 3.1. Courier Revenue Automation
- **Scenario:** A `Waybill` transitions its status to `Delivered`.
- **Validation:** Tests ensure that the `post_save` signal creates an atomic `JournalEntry` hitting Account `1100` (Debit) and `4000` (Credit) exactly matching the Waybill's calculated `price`.

### 3.2. Freight AP/AR Split Automation
- **Scenario:** A multi-leg `FreightBooking` transitions its status to `Delivered`.
- **Validation:** 
  - Generates Accounts Receivable (AR) for the total freight revenue charged to the Shipper.
  - Automatically sweeps through associated `FreightLeg` records and generates Accounts Payable (AP) liability journal entries against Account `2000` (Credit) and `5000` (Debit) for each third-party Carrier utilized in the journey.

### 3.3. 3PL Warehouse Billing
- **Scenario:** A warehouse worker marks a `PutawayTask` as `Completed`.
- **Validation:** Verifies the generation of a handling fee revenue Journal Entry. It calculates the fee based on the volume processed (`quantity * fee rate`) and immediately books it against the Client's AR account.

### 3.4. Financial Dashboard Verification
- **Scenario:** The Financial Controller loads the Logistics Finance Dashboard (`/finance/logistics/`).
- **Validation:** Tests the HTTP response to ensure that the template correctly fetches and isolates logistics-specific `JournalEntryLine` queries (filtering out irrelevant POS/Retail entries) and accurately renders the context variables (`ar_lines`, `ap_lines`).
