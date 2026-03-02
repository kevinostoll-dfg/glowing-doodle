# ---------- build stage ----------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy shared library
COPY shared/ /app/shared/

# Copy application code
COPY services/api-gateway/app/ /app/app/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
