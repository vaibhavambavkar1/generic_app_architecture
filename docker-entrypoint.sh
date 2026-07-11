#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running Database Migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting Static Files..."
python manage.py collectstatic --noinput

# Execute the main command passed to the docker container (e.g. gunicorn)
exec "$@"
