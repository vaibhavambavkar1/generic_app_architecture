# HRMS (Human Resources Management System) — Testing Guide

This guide provides a step-by-step walkthrough to test the Generic ERP HRMS module. This module covers the complete employee lifecycle from recruitment (ATS) to offboarding, including Leave Requests, Expenses, Payroll, and Performance Appraisals.

## Prerequisites
Ensure the application is running via Docker:
```bash
docker compose up -d
```
All URLs referenced below assume the application is accessible at `http://localhost:8000`.

---

## Phase 1: Recruitment (Applicant Tracking System - ATS)

1. **Create a Job Posting**
   - Navigate to your Django Admin dashboard: [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Go to **HRMS** > **Job Postings** and click **Add Job Posting**.
   - **Title**: `Senior Software Engineer`
   - **Department**: `Engineering`
   - **Location**: `Remote`
   - Click **Save**.

2. **Track a Candidate Workflow**
   - Go to **HRMS** > **Candidates** and click **Add Candidate**.
   - Select the `Senior Software Engineer` Job.
   - Enter dummy details (e.g., `Jane Doe`, `jane@example.com`).
   - Click **Save**.
   - Progress the Candidate through the FSM lifecycle using the custom transition buttons:
     - `Applied` ➔ `Phone Screen`
     - `Phone Screen` ➔ `Technical Interview`
     - `Technical Interview` ➔ `Offer Extended`
     - `Offer Extended` ➔ `Hired`

---

## Phase 2: Employee Profile & Payroll

1. **Create an Employee Profile**
   - Navigate to **HRMS** > **Employees** and click **Add Employee**.
   - Link the profile to an existing Django `User`.
   - **Employee ID**: `EMP-001`
   - **Department**: `Engineering`
   - **Annual Leave Balance**: `20`
   - Click **Save**.

2. **Configure Salary Structure**
   - Go to **HRMS** > **Salary Structures** and click **Add Salary Structure**.
   - Link it to `EMP-001`.
   - **Base Salary**: `8000.00`
   - **HRA**: `2000.00`
   - **Tax Deductions**: `1500.00`
   - Click **Save**. Note that the `Net Salary` property will dynamically calculate to `8500.00`.

3. **Generate a Payslip**
   - Go to **HRMS** > **Payslips** and click **Add Payslip**.
   - Link it to `EMP-001` and set the **Month** (e.g., `2026-07-01`).
   - Input the structured amounts.
   - Click **Save**.

---

## Phase 3: Leave & Expense Workflows

1. **Submit a Leave Request**
   - Go to **HRMS** > **Leave Requests** and click **Add Leave Request**.
   - **Employee**: Select `EMP-001`.
   - **Leave Type**: `Annual Leave`
   - Select a `Start Date` and `End Date` (e.g., a 3-day window).
   - Click **Save**.

2. **Process the Leave Request**
   - Open the Leave Request and progress the FSM:
     - `Draft` ➔ `Pending Manager`
     - `Pending Manager` ➔ `Pending HR`
     - `Pending HR` ➔ `Approved`
   - **Verification**: Go back to the `EMP-001` Employee Profile and verify that the `annual_leave_balance` automatically decremented by exactly 3 days.

3. **Submit an Expense Claim**
   - Go to **HRMS** > **Expense Claims**.
   - **Title**: `Client Dinner`
   - **Amount**: `150.00`
   - Click **Save**, then progress the FSM (`Draft` ➔ `Pending Manager` ➔ `Pending Finance` ➔ `Paid`).

---

## Phase 4: Performance Appraisals & OKRs

1. **Initialize an Appraisal Cycle**
   - Go to **HRMS** > **Performance Appraisals** and click **Add**.
   - Select `EMP-001`.
   - **Review Period**: `Q3 2026`
   - Add inline **OKRs** at the bottom (e.g., `Increase test coverage to 90%`).
   - Click **Save**.

2. **Complete the Appraisal Workflow**
   - Open the Appraisal and progress it through the FSM:
     - `Draft` ➔ `Self-Assessment` (Employee fills their evaluation)
     - `Self-Assessment` ➔ `Manager Review` (Manager provides feedback and a 1-5 rating)
     - `Manager Review` ➔ `HR Approval`
     - `HR Approval` ➔ `Completed`
