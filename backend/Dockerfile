FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libimage-exiftool-perl && rm -rf /var/lib/apt/lists/*
COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -e /app/backend
COPY backend /app/backend
COPY data /app/data
COPY db /app/db
COPY models /app/models

ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
