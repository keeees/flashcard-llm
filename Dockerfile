# Use a multi-stage build for optimal image size and security

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
# Copy frontend package files
COPY frontend/package*.json ./
# Install dependencies
RUN npm install
# Copy frontend source
COPY frontend/ ./
# Build frontend
RUN npm run build

# Stage 2: Build Backend and Final Image
FROM python:3.12-slim

# Install system build dependencies (some wheels may need compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python dependency definitions
COPY requirements.txt ./

# Install Python dependencies
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY src/ ./src/

# Copy built frontend assets from previous stage
# This assumes src/api.py is configured to serve static files from /app/frontend/build
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Set environment variables
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose the port
EXPOSE $PORT

# Command to run the application
CMD sh -c "uvicorn src.api:app --host $HOST --port $PORT"
