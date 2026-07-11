FROM django-base:1.0

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["gunicorn","erp_framework.wsgi:application","--bind","0.0.0.0:8000"]