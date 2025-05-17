FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API Gateway code
COPY api-gateway/ .

# Copy the cloud_integrations.py file from the parent directory
COPY cloud_integrations.py .

# Ensure mock_data directory exists
RUN mkdir -p mock_data

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CLOUD_OPTIMIZER_SIMULATION=true
ENV CLOUD_OPTIMIZER_FORCE_SIMULATION=true

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
