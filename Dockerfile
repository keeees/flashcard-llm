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

# Install uv for fast python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy python dependency definition
COPY pyproject.toml uv.lock ./

# Install python dependencies using uv
# --system installs into system python, avoiding venv complexity in docker
# --deploy ensures lock file is respected
RUN uv pip install --system --require-hashes -r pyproject.toml

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
# Use sh to expand environment variables
CMD sh -c "uvicorn src.api:app --host $HOST --port $PORT"
