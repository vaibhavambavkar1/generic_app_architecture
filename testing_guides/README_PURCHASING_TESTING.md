# Purchasing & Procurement — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP Purchasing module. It demonstrates the complete **Procure-to-Pay (P2P)** workflow, including automated Three-Way Matching (Purchase Order ➔ Goods Receipt ➔ Supplier Bill), and how it intrinsically triggers Stock Ledgers and Financial Journal Entries.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

*Note: Ensure you have at least one `Supplier`, one `Product`, and one `Warehouse` configured (from the Inventory and Generic Store Mgmt modules) before beginning.*

---

## Phase 1: Purchase Requisition & Sourcing

1. **Submit an Internal Purchase Request (PR)**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **Purchasing** > **Purchase Requests** and click **Add**.
   - **Department**: `Engineering`
   - **Expected Date**: Set to next week.
   - Add inline items selecting a product and quantity.
   - Click **Save**.
   - Use the FSM transition buttons to move it: `Draft` ➔ `Submitted` ➔ `Approved`.

2. **Generate an RFQ (Optional Sourcing)**
   - Go to **Purchasing** > **Request For Quotations** and click **Add**.
   - Link the approved `Purchase Request`.
   - Add multiple target suppliers to the Many-to-Many field.
   - Save and transition the state: `Draft` ➔ `Sent`.

---

## Phase 2: Purchase Order (PO) Execution

1. **Issue a Purchase Order**
   - Go to **Purchasing** > **Store Purchase Orders** and click **Add**.
   - **Supplier**: Select your test supplier.
   - **Warehouse**: Select the destination warehouse (e.g., `Main Hub`).
   - Add inline `Store PO Line Items` (e.g., Product: `TechCorp ProBook 15`, Quantity: `10`, Unit Price: `800.00`).
   - Click **Save**.
   
2. **Dispatch the PO**
   - Open the PO and click the **Issue PO** FSM transition button.
   - **Result**: The status transitions to `Issued`, formally committing the procurement.

---

## Phase 3: Three-Way Matching (GRN & Billing)

The system enforces automated integrations upon receiving goods and verifying bills.

1. **Step 1: Goods Receipt Note (GRN)**
   - Go to **Purchasing** > **Goods Receipt Notes** and click **Add**.
   - Select the **Purchase Order** you just issued.
   - Enter a `Supplier Challan Number`.
   - In the inline lines, enter the `Received Quantity` matching the PO expectations.
   - Click **Save**.
   - Now click the **Receive Goods** FSM transition button (`Draft` ➔ `Received`).
   
   > **Automated Integration Checks**:
   > 1. **Inventory**: Navigate to `Inventory > Stock Ledgers`. Verify that the system automatically added the received quantity into the Warehouse.
   > 2. **Finance**: Navigate to `Finance > Journal Entries`. Verify that a `JE-GRN-***` entry was generated, automatically debiting the Inventory Asset (`1200`) and crediting Accounts Payable (`2000`).
   > 3. **PO Status**: Check the original PO; it automatically transitioned to `Fully Received` (or `Partially Received` if quantities were short).

2. **Step 2: Supplier Bill (Invoice Verification)**
   - Go to **Purchasing** > **Supplier Bills** and click **Add**.
   - Link both the **Purchase Order** and the **GRN** created earlier.
   - Set the `Due Date` and input the `Subtotal` and `Tax` matching the supplier's physical invoice.
   - Click **Save**.
   - Click the **Verify Bill** FSM transition button (`Draft` ➔ `Verified`).
   
   > **Automated Financial Check**:
   > Navigate to `Finance > Journal Entries` and locate the `JE-BILL-***` entry. The system has automatically generated a journal entry debiting your Expense/Clearing account, debiting Tax Input, and crediting the final Accounts Payable liability for the Supplier.
