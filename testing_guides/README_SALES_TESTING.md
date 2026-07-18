# Sales & POS — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP Sales module. This module governs the entire Quote-to-Cash process, handling both long-cycle B2B workflows (Quotations -> Sales Orders -> AR Invoices) and rapid B2C Point-of-Sale (POS) checkouts with instant inventory and financial ledger integrations.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

*Note: Ensure you have at least one `Customer` (CRM), one `Product` (Generic Store Mgmt), and a `Warehouse` with existing stock (Inventory).*

---

## Phase 1: B2B Quote-to-Order Pipeline

1. **Create a Quotation**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **Sales** > **Quotations** and click **Add Quotation**.
   - **Customer**: Select a test customer.
   - **Valid Until**: Set a future date.
   - Add inline `Quotation Line Items` (e.g., `TechCorp ProBook 15`, Qty `5`, Unit Price `1200.00`).
   - Click **Save**.
   - Progress the FSM: `Draft` ➔ `Sent` ➔ `Accepted`.

2. **Generate the Sales Order (SO)**
   - Go to **Sales** > **Sales Orders** and click **Add Sales Order**.
   - **Customer**: Select the same customer.
   - **Quotation**: Link the accepted quote.
   - **Warehouse**: Select `Main Hub`.
   - Replicate the inline line items.
   - Click **Save**.
   - Progress the FSM: `Draft` ➔ `Confirmed` ➔ `Shipped`.

---

## Phase 2: Formal B2B Invoicing & Accounts Receivable (AR)

1. **Issue a B2B Sales Invoice**
   - Go to **Sales** > **B2B Sales Invoices** and click **Add**.
   - **Customer**: Link the test customer.
   - **Sales Order**: Link the shipped Sales Order.
   - **Due Date**: Next month.
   - Set the `Subtotal`, `Tax`, and `Total Amount` according to the items.
   - Click **Save**.

2. **Verify Financial Automation (AR)**
   - Open the new invoice and click the **Issue Invoice** FSM transition button (`Draft` ➔ `Sent`).
   - **Automated Check**: Navigate to **Finance** > **Journal Entries**.
   - Locate the `JE-INV-***` entry. 
   - Verify that the system automatically generated a balanced double-entry journal: Debiting `1100 - Accounts Receivable` (with the Customer linked to the line item) and Crediting `4000 - Revenue` and `2100 - Tax`.

---

## Phase 3: Rapid POS (Point of Sale) Checkout

Unlike B2B flows, POS invoices instantly deduct stock and recognize cash revenue bypassing the AR lifecycle.

1. **Execute a POS Sale**
   - Go to **Sales** > **POS Invoices** and click **Add**.
   - **Warehouse**: Select `Downtown Store`.
   - Add inline line items (e.g., Qty `1` of `TechCorp ProBook 15`).
   - Fill in the **Total Amount**.
   - (Optional) Select a Payment Method and check **Is Paid**.
   - Click **Save**.

2. **Verify POS Automation (Inventory + Finance)**
   - **Stock Deduction**: Navigate to **Inventory** > **Stock Ledgers**. You will see a new entry with transaction type `SALES` carrying a *negative* quantity, immediately deducting the sold item from the `Downtown Store`.
   - **Cash Recognition**: Navigate to **Finance** > **Journal Entries**. You will see a `JE-POS-***` entry automatically Debiting `1000 - Cash` and Crediting `4000 - Revenue`, instantly finalizing the financial books for the walk-in sale.
