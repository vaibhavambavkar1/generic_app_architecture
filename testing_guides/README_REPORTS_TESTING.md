# Reports & Analytics — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP Reports module. This module serves as the central intelligence hub, aggregating data across Sales, Inventory, and Finance to generate real-time dashboards and formal financial statements.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

*Note: For the best testing experience, ensure you have completed the workflows in the **Sales**, **Purchasing**, and **Finance** testing guides so the database is populated with transactions and journal entries.*

---

## Phase 1: Operational Reports & Dashboards

1. **Executive Dashboard**
   - Navigate to **Reports** > **Executive Dashboard** (or navigate to `http://localhost:8000/reports/dashboard/`).
   - **Metrics to Verify**:
     - **30-Day Revenue**: Aggregates all paid `POSInvoice` totals.
     - **Open Payables**: Fetches the live balance from the `2000 - Accounts Payable` financial account.
     - **Inventory Value**: Fetches the live balance from the `1200 - Inventory` asset account.
     - **Top Products**: Verifies that the dashboard correctly groups and sums the highest grossing line items from recent sales.
     - **Sales Chart**: Ensure the chart renders daily sales data correctly using the integrated Chart.js widget.

2. **Sales & Inventory Reports**
   - Navigate to **Reports** > **Sales Report**. Verify that the list groups total quantities sold and total revenue per product, sorted descending by revenue.
   - Navigate to **Reports** > **Inventory Report**. Verify that the system dynamically aggregates the `StockLedger` (SUM of all IN/OUT quantities) to render the real-time stock-on-hand per product per warehouse.

---

## Phase 2: Core Financial Statements

1. **Trial Balance**
   - Navigate to **Reports** > **Finance Hub** > **Trial Balance**.
   - **Validation**: Ensure that the **Total Debits** exactly equal the **Total Credits** at the bottom of the report. The system calculates this dynamically by scanning all posted `JournalEntryLines`.
   - **Export Test**: Click the **Export to CSV** button (which appends `?export=csv` to the URL) and verify that the downloaded file formats the data cleanly into a spreadsheet.

2. **General Ledger (GL)**
   - Navigate to **Reports** > **Finance Hub** > **General Ledger**.
   - **Validation**: Use the dropdown filter to select a specific account (e.g., `1000 - Cash`). The system should render every individual Debit and Credit line item impacting that specific account across all time.
   - **Export Test**: Click **Export to CSV** to download the ledger history for the selected account.

3. **Income Statement (P&L)**
   - Navigate to **Reports** > **Finance Hub** > **Income Statement**.
   - **Validation**: Verify that it lists all `REVENUE` categorized accounts against all `EXPENSE` categorized accounts. Ensure the dynamically calculated **Net Income** (Revenue minus Expenses) matches expectations.

4. **Balance Sheet**
   - Navigate to **Reports** > **Finance Hub** > **Balance Sheet**.
   - **Validation**: Verify the fundamental accounting equation: `Assets = Liabilities + Equity`. 
   - *Note on Net Income*: The ERP automatically calculates the Current Year Net Income on the fly and injects it into the Equity section to ensure the Balance Sheet always remains perfectly balanced without requiring hard-coded year-end closing entries.
