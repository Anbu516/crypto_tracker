# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for Postgres 
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies 
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder [cite: 3]
COPY --from=builder /install /usr/local
# Copy all project files [cite: 3]
COPY . .

# Environment variables [cite: 3]
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Ensure the script has execution permissions inside the container
RUN chmod +x ./scripts/prestart.sh

EXPOSE 8000

# Use the script as the entry point
CMD ["/bin/bash", "./scripts/prestart.sh"]