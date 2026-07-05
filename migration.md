# Cross-Database Migration Guide

Because this ERP framework is built leveraging the Django ORM, it is largely database-agnostic. Migrating from your current MySQL environment to another relational database (such as PostgreSQL) involves moving data via JSON rather than direct SQL dumps.

This document outlines the standard operating procedure for executing a cross-engine database migration.

---

## Phase 1: Data Extraction

Do **not** use `mysqldump`. Direct SQL dumps contain MySQL-specific syntax that will fail to import into PostgreSQL. Instead, use Django's native serialization.

### Option A: Via the Web UI
1. Log in to the ERP as an Administrator.
2. Navigate to **Administration > Settings**.
3. Click **"Download Full Snapshot"** under the Backups section.
4. Save the generated `.json` file to your server.

### Option B: Via Terminal (For Large Datasets)
Use the `dumpdata` command. We exclude `contenttypes` and `auth.permissions` as they are automatically recreated during migrations and can cause conflict during import.

```bash
docker compose exec web python manage.py dumpdata \
    --format=json \
    --indent=2 \
    --exclude=contenttypes \
    --exclude=auth.permission \
    --exclude=sessions.session \
    --exclude=core.auditlog > erp_migration_data.json
```

---

## Phase 2: Infrastructure Updates

You must update your Docker architecture and application dependencies to support the new database engine (assuming migration to PostgreSQL).

### 1. Update `requirements.txt`
Remove the MySQL driver and add the PostgreSQL driver.
```diff
- mysqlclient>=2.2.0
+ psycopg2-binary>=2.9.9
```

### 2. Update `docker-compose.yml`
Replace the `db` service definition from MySQL to PostgreSQL.
```yaml
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: erp_db
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: erp_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```
*(Remember to update the `volumes` declaration at the bottom of the compose file to `postgres_data`).*

### 3. Update `erp_framework/settings.py` (or `.env`)
Update the `DATABASES` configuration to point to PostgreSQL.
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'erp_db',
        'USER': 'erp_user',
        'PASSWORD': 'erp_password',
        'HOST': 'db',
        'PORT': '5432',
    }
}
```

---

## Phase 3: Schema Initialization

Destroy the old MySQL container and boot the new PostgreSQL container.

```bash
# Stop current environment
docker compose down

# Rebuild the web container with psycopg2 installed
docker compose build web

# Start the new environment
docker compose up -d
```

Initialize the empty PostgreSQL database by running the existing migration files. **Do not create new migrations.**

```bash
docker compose exec web python manage.py migrate
```

---

## Phase 4: Data Restoration

Load the database-agnostic JSON snapshot back into the empty database.

```bash
# Assuming the file is named erp_migration_data.json and is in the app root
docker compose exec web python manage.py loaddata erp_migration_data.json
```

### CRITICAL: PostgreSQL Sequence Reset
*Note: This step is only required for PostgreSQL.*
When using `loaddata`, explicit Primary Key IDs are inserted. PostgreSQL's internal auto-incrementing counters (sequences) do not automatically update to match these inserted IDs. If you do not reset the sequences, the next time a user tries to create a record, PostgreSQL will attempt to assign `ID=1`, resulting in an `IntegrityError`.

Run the following command to generate and execute the sequence reset SQL:

```bash
docker compose exec web python manage.py sqlsequencereset core inventory | docker compose exec -T db psql -U erp_user -d erp_db
```

---

## Phase 5: Verification

1. Log into the web application.
2. Verify that all Purchase Orders, Items, and dynamic configurations (Settings) exist.
3. Test creating a new record (e.g., a new Purchase Order) to confirm that the database ID sequences were reset correctly.
