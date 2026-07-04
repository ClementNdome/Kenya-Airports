# Use an official Python runtime as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PROJ_DIR=/usr/local

# Install system dependencies for pyproj and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libproj-dev \
    proj-bin \
    proj-data \
    libgeos-dev \
    libgdal-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Collect static files (if using Django)
RUN python manage.py collectstatic --noinput

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "your_project.wsgi:application"]