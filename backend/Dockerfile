# backend/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the backend source
COPY app /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn

# Expose FastAPI default port
EXPOSE 8080

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
