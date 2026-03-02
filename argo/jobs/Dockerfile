FROM python:3.11-slim

WORKDIR /app

COPY argo/jobs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY argo/jobs/*.py /app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python"]
