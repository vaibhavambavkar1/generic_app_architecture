# Fleet Management (fleet_mgmt) Testing Guide

## 1. Overview
This document outlines the automated testing procedures for the **Fleet Management (`fleet_mgmt`)** app within the Generic Logistics Management System (LMS). This module is responsible for managing logistical assets like Vehicles, Containers, Driver assignments, and Maintenance tracking.

## 2. Prerequisites & Setup
Before testing the Fleet Management module, ensure the following foundational data configurations:

- **Organization:** A valid Organization record (required by `OrganizationEnforcementMiddleware` / Core Mixins).
- **Users and Employees:** At least one `User` linked to an `Employee` (department: 'Logistics') for testing `DriverAssignment`.
- **Database Backend:** Tests run on the local test database (e.g., MySQL `test_erp_db`). 

To run the tests headlessly via Docker without interactive prompts for database destruction:
```bash
docker exec erp_framework_web_dev python manage.py test fleet_mgmt --noinput
```

## 3. Core Functionality Tested

### 3.1. Asset Creation & Attributes
- **Vehicles:** Verify that vehicles (`Truck (FTL)`, `Delivery Van`, etc.) successfully map their `capacity_kg` and `volume_m3` limits. 
- **Containers:** Verify creation of TEU, FEU, and Reefer container types with active flags.

### 3.2. Vehicle Lifecycle (FSM Transitions)
The tests ensure the `django_fsm` workflow guards against invalid asset states.
- **Valid Transitions Evaluated:**
  - `Available` ➔ `Dispatched` (When assigned to an active route/manifest).
  - `Dispatched` ➔ `In Maintenance` (When flagged for repairs).
  - `In Maintenance` ➔ `Available` (Post-maintenance).
  - Any State ➔ `Out of Service` (Decommissioning).

### 3.3. HRMS Integration (Driver Assignment)
- **Driver Assignments:** Tests validate that the `DriverAssignment` model effectively links an `hrms.Employee` to a `fleet_mgmt.Vehicle` with a valid `assigned_from` timestamp.

### 3.4. Maintenance Auditing
- **Maintenance Logs:** Verifies that costs and descriptions are correctly linked via a foreign key to a specific `Vehicle`, storing an accurate `date_logged`.

## 4. Troubleshooting
If `django.core.exceptions.ValidationError` is thrown regarding `owner_name` or `email`, ensure the `setUp()` method in `tests.py` passes all mandatory fields to the `Organization` object creation.
