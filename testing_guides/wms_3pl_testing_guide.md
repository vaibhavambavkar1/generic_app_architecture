# 3PL Warehouse Management (`wms_3pl`) Testing Guide

## 1. Overview
This document outlines the testing suite for the **3PL Warehouse Management (`wms_3pl`)** app within the Generic Logistics Management System (LMS). This module is responsible for managing multi-tenant bin-level inventory tracking, putaway tasks, and pick-and-pack workflows.

## 2. Prerequisites & Setup
Before executing the tests, ensure the following core configuration data exists in the system:
- **Organization:** A valid Organization record to bypass the global CRM middleware.
- **Master Data:** An active `Customer` (the 3PL Client), an `Employee` (Warehouse Worker), and a `Product` mapping to a `Category` and `UnitOfMeasure`.
- **Infrastructure:** Core `Warehouse` records must exist in the `inventory` app to link the granular `WarehouseZone` ➔ `Aisle` ➔ `Rack` ➔ `Bin` topology.

To run the test suite headlessly in Docker without database destruction prompts:
```bash
docker exec erp_framework_web_dev python manage.py test wms_3pl --noinput
```

## 3. Core Functionality Tested

### 3.1. Warehouse Topology Construction
- **Scenario:** The physical mapping of the warehouse location.
- **Validation:** Tests ensure that the foreign key relationships are strictly maintained from a global `Warehouse` down to a specific `Bin`, and that the `__str__` representations format beautifully (e.g., `North Facility - Zone A - Aisle A1 - Rack R1 - Bin B1`).

### 3.2. Putaway Task Workflow & Inventory Increment
- **Scenario:** Receiving stock from a client and placing it into a specific bin.
- **Validation:**
  1. Tests the `django_fsm` state transitions of `PutawayTask`: `Draft` ➔ `Assigned` ➔ `In Progress` ➔ `Completed`.
  2. Ensures that triggering the `complete_putaway()` transition dynamically generates or updates a `ClientInventory` record for the exact `Customer`, `Product`, and `Bin` location, correctly summing the quantity.

### 3.3. PickList Workflow & Inventory Deduction
- **Scenario:** Pulling stock from bins to fulfill an outbound order (like a Courier Waybill or Freight shipment).
- **Validation:**
  1. Tests the FSM state transitions of `PickList`: `Draft` ➔ `Assigned` ➔ `Picking` ➔ `Packed` ➔ `Shipped`.
  2. Directly triggers the `mark_picked(qty)` function on a `PickListItem` and asserts that it accurately calculates and immediately deducts the specified quantity from the corresponding `ClientInventory` record.

## 4. Financial Integrations (Out of Scope)
Note that testing the automated billing (Handling Fees / Storage Fees) triggered by these `wms_3pl` events is specifically tested within the `logistics_finance` application via Django signals, not here.
