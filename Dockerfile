# Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app

# Expose the dynamic port set by Railway
EXPOSE $PORT

# Run Uvicorn with dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info"]
