# Production-ready Dockerfile for cost-data-storage service using multi-stage build
FROM python:3.9-slim as builder

WORKDIR /app
# Install bash to ensure compatibility with poetry's commands
RUN apt-get update && apt-get install -y bash
# Set default shell to bash as a login shell so that shell built-ins like export work
SHELL ["/bin/bash", "-c"]
# Copy the service-specific dependency files from the repository root
COPY cost-data-storage-service/pyproject.toml cost-data-storage-service/poetry.lock* ./
# Also copy the helper script from the scripts folder in the repository root
RUN bash -c "pip install --upgrade pip && pip install poetry && poetry export -f requirements.txt --output requirements.txt --without-hashes"
COPY scripts/poetry_export.sh ./
RUN chmod +x poetry_export.sh && /bin/bash -c "./poetry_export.sh"

FROM python:3.9-slim

WORKDIR /app
# Copy the generated requirements.txt from the builder stage
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire cost-data-storage-service folder into the image
COPY cost-data-storage-service/ /app

# Run the cost-data-storage service using gunicorn
CMD ["gunicorn", "cost_data_storage_service.app:app", "--bind", "0.0.0.0:8001"]
