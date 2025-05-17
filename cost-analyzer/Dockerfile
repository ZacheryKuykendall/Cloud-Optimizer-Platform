FROM python:3.9-slim AS builder

WORKDIR /app

# Install system dependencies and clean up
RUN apt-get update && \
    apt-get install -y bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]

# Copy project files and install dependencies
COPY cost-analyzer/pyproject.toml cost-analyzer/poetry.lock* ./
RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install poetry && \
    poetry install --no-interaction --no-ansi && \
    pip freeze > requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cost-analyzer/ .
ENV PYTHON_ENV=development
ENV APP_HOME=/app
EXPOSE 8000
CMD ["python", "main.py"]
