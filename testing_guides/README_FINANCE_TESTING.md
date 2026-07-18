# Finance & Accounting — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP Financial Management module, focusing on the Chart of Accounts (CoA), Double-Entry Journalization, and AR/AP (Accounts Receivable & Accounts Payable) payment allocations.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

---

## Phase 1: Chart of Accounts (CoA) Setup

To perform double-entry journalization, core accounts must be configured. By default, the system relies on specific account codes (`1000` for Cash, `1100` for AR, `2000` for AP).

1. **Create the Cash Account**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **Finance** > **Accounts** and click **Add Account**.
   - **Code**: `1000`
   - **Name**: `Cash & Equivalents`
   - **Category**: `Asset`
   - Click **Save and add another**.

2. **Create the AR (Accounts Receivable) Account**
   - **Code**: `1100`
   - **Name**: `Accounts Receivable`
   - **Category**: `Asset`
   - Click **Save and add another**.

3. **Create the AP (Accounts Payable) Account**
   - **Code**: `2000`
   - **Name**: `Accounts Payable`
   - **Category**: `Liability`
   - Click **Save**.

---

## Phase 2: Manual Double-Entry Journalization

1. **Create a Manual Journal Entry**
   - Navigate to **Finance** > **Journal Entries** and click **Add Journal Entry**.
   - Leave the **Entry Number** blank (it auto-generates).
   - **Reference**: `MANUAL-FUNDS-01`
   - **Notes**: `Initial Owner Capital Injection`
   - Check **Is Posted**.

2. **Add Debit and Credit Lines**
   - In the **Lines** inline section:
     - **Line 1 (Debit)**: Select `1000 - Cash & Equivalents`. Enter **Debit**: `50000.00`, **Credit**: `0.00`.
     - **Line 2 (Credit)**: You'll need to create an Equity account on the fly (or beforehand), but for test purposes, you can credit AP (`2000`). Enter **Debit**: `0.00`, **Credit**: `50000.00`.
   - Click **Save**.
   - *Note: If debits and credits do not balance, the `clean()` validation will strictly prevent saving the record.*

3. **Verify Account Balances**
   - Navigate back to **Finance** > **Accounts**.
   - Open the `Cash & Equivalents` account and verify via the Admin UI or Django Shell that the dynamic `.balance` property correctly reflects `50000.00`.

---

## Phase 3: Automated Sub-Ledger Allocations (AR / AP)

When payments are made against Sales Invoices or Supplier Bills, the system automates double-entry journals.

1. **Simulate a Customer Payment (Accounts Receivable)**
   - Assuming you have generated a `B2BSalesInvoice` and a `PaymentTransaction` in the CRM/Sales modules.
   - Go to **Finance** > **Invoice Payment Allocations** and click **Add**.
   - Link the **Payment** to your existing transaction.
   - Select the target **Sales Invoice**.
   - Enter the **Allocated Amount**.
   - Click **Save**.
   
2. **Review the Automated AR Journal Entry**
   - Head to **Finance** > **Journal Entries**.
   - You will see a newly generated system entry prefixed with `JE-PAY-AR-`.
   - Open it and verify the lines: The system automatically debited `1000 - Cash` and credited `1100 - AR`, whilst correctly attaching the **Customer** directly to the line item for sub-ledger reporting.

3. **Simulate a Supplier Payment (Accounts Payable)**
   - Go to **Finance** > **Invoice Payment Allocations** and click **Add**.
   - Link a Payment transaction and a **Supplier Bill**.
   - Click **Save**.
   
4. **Review the Automated AP Journal Entry**
   - Return to **Finance** > **Journal Entries**.
   - Open the new entry prefixed with `JE-PAY-AP-`.
   - Verify the lines: The system automatically debited `2000 - AP` (reducing the liability) and credited `1000 - Cash` (reducing the asset), attaching the **Supplier** to the AP line item.
