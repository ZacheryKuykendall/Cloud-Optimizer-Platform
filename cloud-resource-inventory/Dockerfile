# Production-ready Dockerfile for cloud-resource-inventory service using multi-stage build
FROM python:3.9-slim as builder

WORKDIR /app
# Install bash to ensure compatibility with poetry's commands
RUN apt-get update && apt-get install -y bash
# Set the default shell to bash for subsequent RUN commands
SHELL ["/bin/bash", "-c"]
# Copy dependency definitions; poetry.lock is optional if available
COPY cloud-resource-inventory/pyproject.toml cloud-resource-inventory/poetry.lock* ./
# Run pip and poetry commands using bash
RUN bash -c "pip install --upgrade pip && pip install poetry && poetry export -f requirements.txt --output requirements.txt --without-hashes"
COPY scripts/poetry_export.sh ./
RUN chmod +x poetry_export.sh && /bin/bash -c "./poetry_export.sh"

FROM python:3.9-slim

WORKDIR /app
# Install production dependencies from the exported requirements.txt
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Run the cloud-resource-inventory service using gunicorn on port 8002
CMD ["gunicorn", "cloud_resource_inventory.app:app", "--bind", "0.0.0.0:8002"]
