FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends pkg-config default-libmysqlclient-dev build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["gunicorn","erp_framework.wsgi:application","--bind","0.0.0.0:8000"]