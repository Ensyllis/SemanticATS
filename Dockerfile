# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p data/resumes \
    data/processed_resumes \
    data/errors \
    data/results/storyteller \
    data/results/personality \
    logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "semantic_ats.py"]