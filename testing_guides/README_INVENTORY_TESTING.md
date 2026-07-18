# Inventory Management — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP Inventory Management module, covering Supplier Management, Purchase Orders, and Warehouse Stock Ledgers.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

---

## Phase 1: Supplier & Catalog Configuration

1. **Create a Supplier**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **Inventory** > **Suppliers** and click **Add Supplier**.
   - **Name**: `Acme Wholesale Corp`
   - **Contact Email**: `orders@acmecorp.example.com`
   - **Is Active**: Checked
   - Click **Save**.

2. **Create an Inventory Item**
   - Go to **Inventory** > **Inventory Items** and click **Add Inventory Item**.
   - **Name**: `Premium Widget 2000`
   - **Unit Price**: `25.00`
   - **Stock Level**: `0`
   - **Reorder Threshold**: `50`
   - *Note: Leave SKU blank; the system will automatically generate a unique SKU and its corresponding barcode/QR code.*
   - Click **Save**.

3. **Link Item to Supplier Catalog**
   - Go to **Inventory** > **Supplier Catalog Items** and click **Add**.
   - Select `Acme Wholesale Corp` and `Premium Widget 2000`.
   - Set the agreed **Price** to `20.00` (wholesale price).
   - Click **Save**.

---

## Phase 2: Purchase Order Workflow

The Purchase Order module uses an FSM (Finite State Machine) to enforce standard procurement workflows: `Draft -> Submitted -> Approved -> Received`.

1. **Create a Draft PO**
   - Go to **Inventory** > **Purchase Orders** and click **Add Purchase Order**.
   - Select `Acme Wholesale Corp` as the supplier.
   - Leave the PO number blank (it auto-generates).
   - In the **Lines** inline form, select `Premium Widget 2000`, set **Quantity** to `100`, and **Unit Price** to `20.00`.
   - Click **Save**. 

2. **Progress the PO Status**
   - Open the newly created PO.
   - Using the custom FSM transition buttons in the Django Admin interface (or programmatically via the Django shell), progress the PO through its states:
     - Click **Submit** (`Draft` ➔ `Submitted`)
     - Click **Approve** (`Submitted` ➔ `Approved`)
     - Click **Receive** (`Approved` ➔ `Received`)

---

## Phase 3: Warehouse & Stock Ledger Operations

1. **Setup Warehouses**
   - Navigate to **Inventory** > **Warehouses** and click **Add Warehouse**.
   - Create a Main Distribution Center: **Name**: `Main Hub`.
   - Create a Retail Outlet: **Name**: `Downtown Store`.

2. **Execute a Stock Adjustment**
   - Go to **Inventory** > **Stock Adjustments** and click **Add Stock Adjustment**.
   - Select `Main Hub` and the `Premium Widget 2000` product.
   - Set **Reason** to `Initial Stock Check`.
   - Set **Quantity Adjusted** to `500`.
   - Save the record, then execute the `Approve` FSM transition to automatically log the adjustment into the **Stock Ledger**.

3. **Execute a Warehouse Transfer**
   - Go to **Inventory** > **Warehouse Transfers** and click **Add Warehouse Transfer**.
   - **From Warehouse**: `Main Hub`
   - **To Warehouse**: `Downtown Store`
   - **Product**: `Premium Widget 2000`
   - **Quantity**: `100`
   - Save the record.
   - Progress the FSM:
     - Click **Dispatch Transfer** (`Draft` ➔ `In Transit`). This automatically creates a negative Stock Ledger entry for the `Main Hub`.
     - Click **Receive Transfer** (`In Transit` ➔ `Completed`). This automatically creates a positive Stock Ledger entry for the `Downtown Store`.

---

## Phase 4: Analytics & Audit

1. **Check the Ledger**
   - Navigate to **Inventory** > **Stock Ledgers**.
   - Verify that all automatic entries (`ADJUST` and `TRANSFER` types) reflect the precise movements configured above.
   
2. **Review Audit Trails**
   - Modify the `Premium Widget 2000` price to `28.00` in the admin.
   - Navigate to **Inventory** > **Inventory Item Price Logs** to confirm the system recorded the historical price change timestamp automatically.
