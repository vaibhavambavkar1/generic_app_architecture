# Enterprise Production Deployment Guidelines

This document outlines the strict Standard Operating Procedures (SOP) for deploying the ERP framework into a live production environment (AWS, DigitalOcean, Azure, etc.).

---

## 1. Security & IP Protection (Source Code Obfuscation)

To protect your Intellectual Property when deploying to client servers or self-hosted environments, this project uses a specialized **Multi-Stage Dockerfile (`Dockerfile.prod`)**.

### How Obfuscation Works:
1. **Compilation Phase:** The Docker build process compiles every single `.py` file into compiled python bytecode (`.pyc`).
2. **Deletion Phase:** It aggressively deletes all original human-readable `.py` files.
3. **Runtime Phase:** The final Docker image contains **only** the unreadable `.pyc` files. Python's native import system understands how to execute `.pyc` files natively via Gunicorn.
*Note: This prevents anyone with access to the server from reading your proprietary business logic, workflow rules, or licensing mechanisms.*

---

## 2. Infrastructure Setup

### Prerequisites
*   A Linux VPS (Ubuntu 22.04 LTS recommended)
*   Docker & Docker Compose V2 installed
*   An SSL/TLS Certificate (via Let's Encrypt or Cloudflare)

### Step 1: Environment Configuration
Do **not** use the development `docker-compose.yml` or `.env` files.
1. SSH into your production server.
2. Clone the repository.
3. Copy the production template: `cp .env.example .env`
4. **CRITICAL:** Edit `.env` and set `DEBUG=False`. Generate a highly secure random string for `SECRET_KEY`. Set `ALLOWED_HOSTS` to your actual domain name (e.g., `erp.yourcompany.com`).

### Step 2: Build & Deploy
Launch the environment using the production-specific compose file:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
This boots up the obfucated Gunicorn Web Server, MySQL 8.0, Redis, and the highly concurrent Celery workers.

### Step 3: Initialize Database
Because the original `manage.py` was deleted during obfuscation, you must run commands against the compiled `manage.pyc` file:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.pyc migrate
docker compose -f docker-compose.prod.yml exec web python manage.pyc createsuperuser
```

---

## 3. Web Server & Static Files (Nginx)

Gunicorn is excellent for executing Python code, but terrible at serving static files (CSS, JS, Images). You must place an Nginx Reverse Proxy in front of Gunicorn.

### 1. Collect Static Files
Extract the static files from the Docker container to the host machine:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.pyc collectstatic --noinput
```

### 2. Sample Nginx Configuration (`/etc/nginx/sites-available/erp`)
```nginx
server {
    listen 80;
    server_name erp.yourcompany.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # Serve Static Files Directly via Nginx (Fast)
    location /static/ {
        root /path/to/your/generic_workflow_app;
    }

    # Pass all other requests to Gunicorn inside Docker
    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 4. Scaling the Architecture

If your user base grows beyond what a single server can handle:
1. **Database:** Move the MySQL service out of Docker and onto a managed database provider (like AWS RDS). Update the `.env` file to point to the AWS endpoint.
2. **Media Storage:** If users are uploading files (Profile Pictures, Invoices), you **must** configure AWS S3. If you run multiple Gunicorn containers across different servers, local file uploads will not sync between them. (See the S3 variables in `.env.example`).
3. **Celery:** You can horizontally scale background processing simply by spinning up more Celery worker containers:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --scale celery-worker=3
   ```
