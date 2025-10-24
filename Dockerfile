FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential bash && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
EXPOSE 8000

# ✅ main fix: resolve the port variable before passing to uvicorn
ENTRYPOINT ["bash", "-c"]
CMD ["uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
