# Helpdesk — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP Helpdesk module, focusing on ticket categorization, FSM (Finite State Machine) lifecycle states, and internal/external communication threads.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

---

## Phase 1: Configuration

1. **Create Ticket Categories**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **Helpdesk** > **Ticket Categories** and click **Add Ticket Category**.
   - Create a few logical categories, for example:
     - **Name**: `Technical Support`
     - **Name**: `Billing Inquiry`
     - **Name**: `Feature Request`
   - Click **Save**.

---

## Phase 2: Ticket Creation & Assignment

1. **Submit a New Ticket**
   - Navigate to **Helpdesk** > **Tickets** and click **Add Ticket**.
   - **Title**: `Cannot access my premium account features`
   - **Description**: `I upgraded to premium yesterday, but the dashboard still shows me as a free user. Please fix this ASAP.`
   - **Category**: Select `Billing Inquiry`.
   - **Priority**: Select `High`.
   - **Reporter**: Select your current test user account.
   - Leave **Assignee** and **Resolution Notes** blank for now.
   - Click **Save**. The ticket is automatically placed in the `Open` state.

2. **Assign the Ticket (FSM Transition)**
   - Open the newly created ticket from the list.
   - You will see custom FSM transition buttons at the top right of the Django Admin.
   - *Note: To transition to "In Progress", the system requires an Assignee.*
   - Edit the ticket, select a user for the **Assignee** field, and click **Save**.
   - Now, click the **Assign Ticket** transition button to progress the status: `Open` ➔ `In Progress`.

---

## Phase 3: Communication & Comments

1. **Add an External (Public) Comment**
   - Scroll down to the **Ticket Comments** inline form.
   - **Author**: Select a user (e.g., the assignee).
   - **Body**: `We are currently investigating your account sync issue with our payment provider.`
   - Leave **Is internal** unchecked.
   - Click **Save**.

2. **Add an Internal (Staff-Only) Note**
   - Add another comment in the inline form.
   - **Author**: Select a staff member.
   - **Body**: `Looks like the webhook failed from Stripe. I'm manually running the sync script.`
   - Check the **Is internal** box.
   - Click **Save**. (In the customer-facing frontend, this comment will be hidden from the reporter).

---

## Phase 4: Resolution & Closure

1. **Mark as Resolved**
   - Once the issue is fixed, fill out the **Resolution Notes** field: `Manual sync complete. The account is now successfully upgraded to premium.`
   - Click **Save**.
   - Click the **Mark Resolved** FSM transition button (`In Progress` ➔ `Resolved`).

2. **Close the Ticket**
   - After the user confirms the fix (or after a timeout period), click the **Close Ticket** transition button (`Resolved` ➔ `Closed`).

3. **Reopening (Optional)**
   - If the issue persists, test the FSM fallback by clicking **Reopen Ticket**, which instantly transitions the ticket from any state back to `Open`.
