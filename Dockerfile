# Dockerfile for Exercise Planner & Tracker Agent (ADK)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set environment defaults
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Default command runs main in interactive or server mode
CMD ["python", "main.py", "--mode=interactive"]
