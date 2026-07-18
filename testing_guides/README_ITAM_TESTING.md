# ITAM (IT Asset Management) — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP ITAM module. This module enables the strict tracking of hardware and software assets, their maintenance lifecycles, and their physical assignments to employees via FSM transitions.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

*Note: You must have an active `Employee` profile created in the HRMS module to test asset assignments.*

---

## Phase 1: Configuration & Asset Procurement

1. **Create an Asset Category**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **Itam** > **Asset Categories** and click **Add Asset Category**.
   - **Name**: `Laptops`
   - **Description**: `Company issued developer and executive laptops.`
   - Click **Save**.

2. **Register a New IT Asset**
   - Go to **Itam** > **Assets** and click **Add Asset**.
   - **Name**: `MacBook Pro M3 Max`
   - **Category**: `Laptops`
   - **Serial Number**: `C02XYZ987654`
   - Leave **Barcode** blank (it will automatically generate as `AST-C02XYZ987654`).
   - **Purchase Cost**: `3200.00`
   - Leave **Current Assignee** blank.
   - Click **Save**. The asset will default to the `Draft` state.

---

## Phase 2: Asset Lifecycle & Employee Assignments

The ITAM module uses Finite State Machines (FSM) to strictly control an asset's state (`Available` ➔ `In Use` ➔ `Under Maintenance` ➔ `Retired`).

1. **Make Asset Available**
   - Open the newly created asset.
   - Use the FSM transition button to move it from `Draft` to `Available` (if your system implements the initial pipeline), or verify that it is natively accessible for assignment.

2. **Assign Asset to an Employee (Check-Out)**
   - Edit the asset and select a valid HRMS **Employee** in the `Current assignee` field.
   - Click **Save**.
   - Now click the **Assign Asset** FSM transition button.
   - **Result**: The asset state transitions to `In Use`.
   - **Verification**: Go to **Itam** > **Asset Assignments** to verify that a historical audit log was automatically created linking this employee, asset, and today's check-out date.

3. **Return Asset (Check-In)**
   - Open the asset record again.
   - Click the **Return Asset** FSM transition button.
   - **Result**: The state reverts to `Available`, and the `Current assignee` field is automatically cleared.

---

## Phase 3: Maintenance & End of Life

1. **Send for Maintenance**
   - With the asset in the `Available` (or `In Use`) state, click the **Send to Maintenance** transition button.
   - **Result**: The state transitions to `Under Maintenance`.

2. **Log a Maintenance Record**
   - Go to **Itam** > **Maintenance Records** and click **Add**.
   - **Asset**: `MacBook Pro M3 Max`
   - **Date**: Today's Date.
   - **Cost**: `150.00`
   - **Description**: `Replaced faulty keyboard trackpad.`
   - Click **Save**.
   - Return to the Asset and use the FSM transition to move it back to `Available`.

3. **Retire the Asset**
   - Simulate end-of-life for the asset.
   - Open the asset and click the **Retire Asset** FSM transition button.
   - **Result**: The state moves permanently to `Retired`, automatically un-assigning any employees if it was still in use.
