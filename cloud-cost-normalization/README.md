# Cloud Cost Normalization Service

A Python library for normalizing and standardizing cloud costs across different providers (AWS, Azure, GCP). This service helps organizations understand and analyze their cloud spending by providing a unified view of costs across multiple cloud platforms.

## Features

- **Multi-Cloud Support**: Normalize costs from AWS, Azure, and GCP into a standardized format
- **Resource Type Mapping**: Map provider-specific resource types to standardized categories
- **Currency Conversion**: Convert costs to a common currency with exchange rate caching
- **Cost Aggregation**: Group and analyze costs by various dimensions
- **Type Safety**: Full type hints and Pydantic models for reliable data handling
- **Async Support**: Asynchronous operations for efficient data processing
- **Extensible**: Easy to add support for additional cloud providers

## Installation

```bash
pip install cloud-cost-normalization
```

## Requirements

- Python 3.9+
- Dependencies:
  - pydantic>=2.0.0
  - sqlalchemy>=2.0.0
  - alembic>=1.9.0
  - pandas>=2.0.0
  - requests>=2.28.0
  - python-dateutil>=2.8.2
  - aws-cost-explorer-client>=0.1.0
  - azure-mgmt-costmanagement>=3.0.0
  - google-cloud-billing>=1.9.0
  - forex-python>=1.8.0
  - rich>=13.0.0

## Quick Start

```python
from datetime import datetime, timedelta
from cloud_cost_normalization import CloudCostNormalizer
from cloud_cost_normalization.models import CloudProvider

# Initialize clients for each provider
aws_client = AWSCostExplorerClient(...)
azure_client = AzureCostManagementClient(...)
gcp_client = GCPBillingClient(...)

# Create normalizer
normalizer = CloudCostNormalizer(
    aws_client=aws_client,
    azure_client=azure_client,
    gcp_client=gcp_client,
    target_currency="USD"
)

# Set time range
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)

# Get normalized costs from each provider
aws_costs = await normalizer.normalize_costs(
    provider=CloudProvider.AWS,
    start_time=start_time,
    end_time=end_time
)

azure_costs = await normalizer.normalize_costs(
    provider=CloudProvider.AZURE,
    start_time=start_time,
    end_time=end_time
)

gcp_costs = await normalizer.normalize_costs(
    provider=CloudProvider.GCP,
    start_time=start_time,
    end_time=end_time
)

# Combine all costs
all_costs = aws_costs + azure_costs + gcp_costs

# Aggregate costs by provider and resource type
aggregation = await normalizer.aggregate_costs(
    entries=all_costs,
    group_by=["resource.provider", "resource.type"]
)

# Print results
print(f"Total Cost: ${aggregation.total_cost:.2f} {aggregation.currency}")
for group, cost in aggregation.costs.items():
    print(f"{group}: ${cost:.2f}")
```

## Normalized Cost Structure

The service normalizes cloud costs into a standardized format:

```python
NormalizedCostEntry(
    id="aws-i-1234567890",
    account_id="123456789012",
    resource=ResourceMetadata(
        provider=CloudProvider.AWS,
        provider_id="i-1234567890",
        name="web-server",
        type=ResourceType.COMPUTE,
        region="us-east-1",
        billing_type=BillingType.ON_DEMAND,
        specifications={
            "instance_type": "t3.micro",
            "os": "Linux"
        }
    ),
    allocation=CostAllocation(
        project="web-app",
        department="engineering",
        environment="production",
        cost_center="12345",
        custom_tags={
            "team": "platform",
            "owner": "john.doe"
        }
    ),
    cost_breakdown=CostBreakdown(
        compute=Decimal("100.00"),
        storage=Decimal("10.00"),
        network=Decimal("5.00"),
        other=Decimal("0.00")
    ),
    currency="USD",
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31)
)
```

## Resource Type Mapping

The service maps provider-specific resource types to standardized categories:

```python
class ResourceType(str, Enum):
    COMPUTE = "compute"      # EC2, Azure VMs, GCP Compute Engine
    STORAGE = "storage"      # S3, Azure Storage, GCP Cloud Storage
    DATABASE = "database"    # RDS, Azure SQL, GCP Cloud SQL
    NETWORK = "network"      # VPC, Azure VNet, GCP VPC
    SERVERLESS = "serverless" # Lambda, Azure Functions, Cloud Functions
    CONTAINER = "container"  # ECS, AKS, GKE
    ANALYTICS = "analytics"  # EMR, HDInsight, BigQuery
    SECURITY = "security"    # WAF, Azure Firewall, Cloud Armor
    MANAGEMENT = "management" # CloudWatch, Monitor, Cloud Monitoring
    OTHER = "other"         # Uncategorized services
```

## Cost Aggregation

The service supports flexible cost aggregation:

```python
# Aggregate by provider
aggregation = await normalizer.aggregate_costs(
    entries=costs,
    group_by=["resource.provider"]
)

# Aggregate by provider and type
aggregation = await normalizer.aggregate_costs(
    entries=costs,
    group_by=["resource.provider", "resource.type"]
)

# Aggregate by environment and cost center
aggregation = await normalizer.aggregate_costs(
    entries=costs,
    group_by=["allocation.environment", "allocation.cost_center"]
)
```

## Currency Conversion

The service automatically handles currency conversion:

```python
normalizer = CloudCostNormalizer(
    aws_client=aws_client,
    azure_client=azure_client,
    gcp_client=gcp_client,
    target_currency="USD",  # All costs will be converted to USD
    currency_service=CurrencyService(
        cache_ttl=3600,  # Cache exchange rates for 1 hour
        base_currency="USD",
        fallback_source="exchangerate-api"  # Fallback source if primary fails
    )
)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-cost-normalization.git
cd cloud-cost-normalization

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_normalizer.py
```

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Linting
pylint src tests
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
