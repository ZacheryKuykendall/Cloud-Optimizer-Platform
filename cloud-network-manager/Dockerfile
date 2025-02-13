# Production-ready Dockerfile for cloud-network-manager service using multi-stage build
FROM python:3.9-slim as builder

WORKDIR /app
# Install bash to ensure compatibility with poetry's commands
RUN apt-get update && apt-get install -y bash
# Set default shell to bash
SHELL ["/bin/bash", "-c"]
# Copy dependency definitions from the service folder
COPY cloud-network-manager/pyproject.toml cloud-network-manager/poetry.lock* ./
# Copy helper script from the repository root
COPY scripts/poetry_export.sh ./
RUN chmod +x poetry_export.sh && /bin/bash -c "./poetry_export.sh"

FROM python:3.9-slim

WORKDIR /app
# Copy the generated requirements.txt from builder stage
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire cloud-network-manager folder into the image
COPY cloud-network-manager/ /app

# Run the cloud-network-manager service using gunicorn on port 8003
CMD ["gunicorn", "cloud_network_manager.app:app", "--bind", "0.0.0.0:8003"]
