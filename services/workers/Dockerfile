FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY shared/ /app/shared/

# Copy service requirements and install
COPY services/workers/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/workers/app/ /app/app/

# Set PYTHONPATH so shared imports resolve
ENV PYTHONPATH=/app

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
