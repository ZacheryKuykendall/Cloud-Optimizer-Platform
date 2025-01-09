# Cost Data Storage Service

A Python service for storing and managing cloud cost data with support for multiple storage backends and data formats. This service provides a robust platform for storing, querying, and analyzing cloud cost data from various providers.

## Features

- Multiple Storage Backends:
  - PostgreSQL
  - MongoDB
  - ClickHouse
  - Elasticsearch
  - Cassandra
  - InfluxDB
  - TimescaleDB
  - DuckDB

- Data Formats:
  - JSON
  - Parquet
  - Avro
  - ORC
  - CSV
  - Arrow

- Storage Management:
  - Data partitioning
  - Retention policies
  - Backup and recovery
  - Maintenance windows
  - Storage metrics

- Cost Data Operations:
  - Batch imports
  - Data validation
  - Format conversion
  - Data aggregation
  - Custom queries

- Performance Features:
  - Query optimization
  - Caching strategies
  - Compression
  - Parallel processing
  - Bulk operations

## Installation

```bash
pip install cost-data-storage-service
```

## Prerequisites

- Python 3.8 or higher
- One or more supported storage backends:
  - PostgreSQL 12+
  - MongoDB 4.4+
  - ClickHouse 21+
  - Elasticsearch 7+
  - Cassandra 4+
  - InfluxDB 2+
  - TimescaleDB 2+
  - DuckDB 0.8+

## Quick Start

### Basic Usage

```python
from cost_storage import (
    StorageConfig,
    StorageBackend,
    StorageFormat,
    CostRecord
)

# Configure storage backend
config = StorageConfig(
    backend=StorageBackend.POSTGRESQL,
    format=StorageFormat.PARQUET,
    connection_string="postgresql://user:pass@localhost/costdb",
    database_name="costdb"
)

# Initialize storage
storage = CostStorageService(config)

# Store cost record
record = CostRecord(
    timestamp=datetime.now(),
    provider="AWS",
    account_id="123456789",
    region="us-east-1",
    service="EC2",
    resource_id="i-1234567890abcdef0",
    resource_type="t3.micro",
    cost_type="COMPUTE",
    amount=Decimal("0.0104"),
    currency="USD"
)

storage.store(record)
```

### Batch Operations

```python
from cost_storage import CostBatch

# Create batch of records
batch = CostBatch(
    records=[record1, record2, record3],
    source="aws-cost-explorer"
)

# Store batch
storage.store_batch(batch)
```

### Querying Data

```python
from cost_storage import (
    QueryFilter,
    AggregationConfig,
    AggregationLevel,
    AggregationDimension
)

# Create query filter
filter = QueryFilter(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    providers=["AWS"],
    services=["EC2", "S3"],
    cost_types=["COMPUTE", "STORAGE"]
)

# Query records
results = storage.query(filter)

# Aggregate costs
config = AggregationConfig(
    time_level=AggregationLevel.DAILY,
    dimensions=[
        AggregationDimension.SERVICE,
        AggregationDimension.REGION
    ]
)

aggregated = storage.aggregate(filter, config)
```

### Data Retention

```python
from cost_storage import RetentionPolicy

# Configure retention policy
policy = RetentionPolicy(
    duration_days=365,
    archive_after_days=90,
    delete_after_days=730,
    compression_enabled=True
)

# Apply policy
storage.set_retention_policy(policy)
```

### Backup Configuration

```python
from cost_storage import BackupConfig

# Configure backups
backup_config = BackupConfig(
    enabled=True,
    frequency="daily",
    retention_days=30,
    storage=StorageConfig(
        backend=StorageBackend.S3,
        format=StorageFormat.PARQUET,
        connection_string="s3://my-bucket/backups"
    )
)

# Apply backup configuration
storage.configure_backup(backup_config)
```

## Advanced Usage

### Custom Storage Backend

```python
from cost_storage import StorageBackend

class CustomStorage:
    def store(self, record: CostRecord) -> None:
        # Implement custom storage logic
        pass

# Register custom backend
storage.register_backend(
    StorageBackend.CUSTOM,
    CustomStorage()
)
```

### Performance Monitoring

```python
# Get storage metrics
metrics = storage.get_metrics()

print(f"Total Records: {metrics.total_records}")
print(f"Total Size: {metrics.total_size_bytes} bytes")
print(f"Query Latency: {metrics.query_latency_ms}ms")
```

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cost-data-storage-service.git
cd cost-data-storage-service
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_storage.py
```

### Code Style

The project uses several tools to maintain code quality:

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy src tests

# Linting
pylint src tests
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [AWS Cost Explorer Client](https://github.com/yourusername/aws-cost-explorer-client)
- [Azure Cost Management Client](https://github.com/yourusername/azure-cost-management-client)
- [GCP Billing Client](https://github.com/yourusername/gcp-billing-client)
- [Cloud Cost Normalization](https://github.com/yourusername/cloud-cost-normalization)
- [Currency Conversion Service](https://github.com/yourusername/currency-conversion-service)

## Acknowledgments

- SQLAlchemy ORM
- Apache Arrow
- DuckDB
- TimescaleDB
- ClickHouse
