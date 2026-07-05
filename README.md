# Universal ERP Framework 🚀

Welcome to the **Universal ERP Framework**! This project is a highly advanced, blazingly fast, and incredibly modular enterprise resource planning (ERP) foundation built to run complex business logic without the bloat of traditional frontend JavaScript frameworks.

## 🛠️ Technology Stack
*   **Backend:** Python & Django
*   **Frontend (UI):** Tailwind CSS & HTMX (for instant, page-reload-free interactions)
*   **Database:** MySQL
*   **Background Jobs:** Celery & Redis
*   **Infrastructure:** Fully containerized with Docker

---

## ✨ Core Features

We didn't just build an app; we built an **Engine**. The `core` app handles all the complex enterprise requirements so you can easily plug in any industry module (like Inventory, HR, or Healthcare) in record time.

1.  **⚙️ Universal Workflow Engine**
    Instead of hardcoding status changes (like "Draft" to "Approved"), we built a dynamic Rule Engine. You can define custom states, transitions, and automatic triggers (like sending emails or firing alerts) directly from the admin panel!
2.  **🕵️ Universal Audit Log**
    Who changed what, and when? Every time a user edits a record, the system automatically tracks the exact changes (old value vs. new value) and securely logs it in the background using Celery. 
3.  **📤 Universal Data Importer & Exporter**
    *   **Export:** Download any database table instantly into professional **PDFs, Excel (.xlsx), CSV, or JSON** files.
    *   **Import:** Upload massive Excel/CSV files directly via the UI to safely mass-create or update records.
4.  **🎛️ Dynamic Configuration Store**
    Need to change a business rule (like `REQUIRE_PO_APPROVAL`)? Don't touch the code! Change the settings globally in the live database via the Settings Dashboard, and the system updates instantly.
5.  **📊 Interactive Analytics (Plotly)**
    Beautiful, interactive charts (Pie, Bar, Line) that load asynchronously into the dashboard without slowing down the initial page load.
6.  **💾 Built-In Backup System**
    Generate completely portable JSON snapshots of your entire database with one click. Safely migrate your data or restore your system if anything goes wrong.

---

## 🚀 How to Run the Application

Because everything is containerized via Docker, setting up this massive system takes less than 2 minutes.

### Prerequisites
Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your machine.

### Installation Steps

1. **Clone the repository and open the folder in your terminal.**
2. **Build and start the services:**
   ```bash
   docker compose up -d --build
   ```
   *This single command automatically starts the MySQL database, Redis cache, Celery background workers, and the Django Web server!*

3. **Initialize the Database Schema:**
   ```bash
   docker compose exec web python manage.py migrate
   ```

4. **Access the App:**
   Open your browser and navigate to: `http://localhost:8000`

---

## 📁 Project Structure

*   `erp_framework/` - The main configuration folder for Django settings and root URLs.
*   `core/` - The heart of the application. Contains the Workflow Engine, Triggers, Audit Logs, Exporters/Importers, and all generic UI components.
*   `inventory/` - A sample domain application built on top of `core` showing how to implement Purchase Orders and Items seamlessly.
*   `docker-compose.yml` - The blueprint that glues the Web Server, Database, and Background Job workers together.

---

## 📖 Additional Documentation
Looking to expand or migrate the architecture? Check out these guides located in the root folder:
*   [Business Expansion Guideline (`guideline.md`)](./guideline.md) - How to build 15 different apps (CRM, HRMS, POS) using this core.
*   [API Migration Guide (`migrate_to_drf.md`)](./migrate_to_drf.md) - How to attach a JSON API for mobile apps.
*   [UI Migration Guide (`ui_migration_guide.md`)](./ui_migration_guide.md) - How to replace HTMX with React/Next.js.
*   [Database Migration Guide (`migration.md`)](./migration.md) - How to safely swap MySQL for PostgreSQL.
