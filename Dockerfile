# Use lightweight Python base image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install build tools (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your FastAPI app folder
COPY app ./app

# Expose the default app port (not required by Railway but good practice)
EXPOSE 8000

# ✅ Start Uvicorn, listening on Railway's assigned port
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
