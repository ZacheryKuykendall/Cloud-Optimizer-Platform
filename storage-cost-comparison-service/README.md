# Storage Cost Comparison Service

A Python service for comparing storage costs across different cloud providers, providing detailed cost analysis, performance metrics, and optimization recommendations.

## Features

- Multi-Cloud Storage Cost Analysis:
  - AWS Storage Services:
    - S3 (Object Storage)
    - EBS (Block Storage)
    - EFS (File Storage)
    - Glacier (Archive Storage)
  - Azure Storage Services:
    - Blob Storage
    - Managed Disks
    - Files
    - Archive Storage
  - Google Cloud Storage Services:
    - Cloud Storage
    - Persistent Disk
    - Filestore
    - Archive Storage
  - Other Providers:
    - Oracle Cloud Storage
    - Alibaba Cloud OSS

- Storage Types Support:
  - Object Storage
  - Block Storage
  - File Storage
  - Archive Storage
  - Data Lake Storage
  - Backup Storage

- Comprehensive Analysis:
  - Cost breakdown
  - Performance metrics
  - Feature comparison
  - Compliance requirements
  - Data redundancy options
  - Access patterns

- Advanced Features:
  - Real-time pricing updates
  - Performance benchmarking
  - Cost optimization recommendations
  - Compliance requirements checking
  - Regional availability analysis

## Installation

```bash
pip install storage-cost-comparison-service
```

## Prerequisites

- Python 3.8 or higher
- Cloud provider credentials:
  - AWS credentials
  - Azure credentials
  - GCP credentials
- Optional dependencies:
  - Redis (for caching)
  - PostgreSQL (for historical data)

## Quick Start

### Basic Storage Comparison

```python
from storage_comparison import (
    ComparisonRequest,
    ComparisonCriteria,
    StorageRequirements,
    StorageType,
    CloudProvider
)

# Configure storage requirements
requirements = StorageRequirements(
    storage_type=StorageType.OBJECT,
    min_capacity_gb=1000.0,
    min_iops=1000,
    min_throughput_mbps=100.0
)

# Create comparison criteria
criteria = ComparisonCriteria(
    requirements=requirements,
    regions=["us-east-1", "us-east", "us-central1"],
    time_period=timedelta(days=30),
    capacity_gb=1000.0
)

# Create comparison request
request = ComparisonRequest(
    criteria=criteria,
    include_performance_metrics=True
)

# Get comparison results
comparator = StorageComparator()
response = comparator.compare(request)

# Process results
print(f"Recommended Option: {response.results.recommended_option.service.service_name}")
print(f"Monthly Cost: ${response.results.recommended_option.monthly_cost}")

# Show alternatives
for alt in response.results.alternatives[:3]:
    print(f"\nAlternative: {alt.service.service_name}")
    print(f"Provider: {alt.service.provider}")
    print(f"Monthly Cost: ${alt.monthly_cost}")
```

### Detailed Cost Analysis

```python
from storage_comparison import StorageTier, DataRedundancy

# Configure detailed comparison
criteria = ComparisonCriteria(
    requirements=StorageRequirements(
        storage_type=StorageType.OBJECT,
        min_capacity_gb=1000.0,
        required_tier=StorageTier.STANDARD,
        redundancy=DataRedundancy.REGION
    ),
    preferred_providers=[CloudProvider.AWS, CloudProvider.AZURE],
    regions=["us-east-1", "us-east"],
    time_period=timedelta(days=365),
    capacity_gb=1000.0,
    expected_growth_rate=0.1  # 10% growth per year
)

# Get detailed comparison
response = comparator.compare_detailed(
    criteria,
    include_performance_metrics=True,
    include_cost_breakdown=True,
    include_savings_analysis=True
)

# Process cost breakdown
for estimate in response.results.estimates:
    print(f"\nService: {estimate.service.service_name}")
    print(f"Provider: {estimate.service.provider}")
    print(f"Storage Cost: ${estimate.cost_breakdown.storage_cost}")
    print(f"Operation Cost: ${estimate.cost_breakdown.operation_cost}")
    print(f"Transfer Cost: ${estimate.cost_breakdown.transfer_cost}")
    
    # Show savings opportunities
    for opportunity, amount in estimate.savings_opportunities.items():
        print(f"Potential Saving ({opportunity}): ${amount}")
```

### Performance Analysis

```python
from storage_comparison import PerformanceMetrics

# Get performance metrics
metrics = response.performance_metrics

for service_id, metric in metrics.items():
    service = next(e for e in response.results.estimates 
                  if e.service.id == service_id)
    
    print(f"\nService: {service.service.service_name}")
    print(f"IOPS Score: {metric.iops_score}")
    print(f"Throughput Score: {metric.throughput_score}")
    print(f"Latency Score: {metric.latency_score}")
    print(f"Availability Score: {metric.availability_score}")
    print(f"Durability Score: {metric.durability_score}")
    print(f"Overall Score: {metric.overall_score}")
```

## Advanced Usage

### Custom Storage Requirements

```python
# Configure custom requirements
requirements = StorageRequirements(
    storage_type=StorageType.BLOCK,
    min_capacity_gb=500.0,
    min_iops=5000,
    min_throughput_mbps=200.0,
    max_latency_ms=10.0,
    required_features={
        "encryption_at_rest",
        "encryption_in_transit",
        "snapshot_support"
    },
    compliance_requirements={
        "hipaa",
        "pci_dss",
        "gdpr"
    }
)

# Create comparison criteria
criteria = ComparisonCriteria(
    requirements=requirements,
    regions=["us-east-1", "us-east"],
    time_period=timedelta(days=365),
    capacity_gb=500.0,
    performance_requirements={
        "min_burst_iops": 10000,
        "max_burst_duration": 30  # minutes
    },
    compliance_requirements={
        "data_residency": "US",
        "encryption_standard": "AES-256"
    }
)
```

### Caching and Performance

```python
# Configure caching
comparator = StorageComparator(
    cache_config={
        "pricing_ttl": 3600,  # 1 hour
        "service_ttl": 86400,  # 24 hours
        "redis_url": "redis://localhost:6379"
    }
)

# Batch comparison
results = comparator.compare_batch(
    requests=[request1, request2, request3],
    parallel=True,
    max_workers=4
)
```

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/storage-cost-comparison-service.git
cd storage-cost-comparison-service
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
pytest tests/test_comparator.py
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
- [Cost Estimation Engine](https://github.com/yourusername/cost-estimation-engine)

## Acknowledgments

- Cloud provider pricing APIs
- Storage benchmarking tools
- Cost analysis libraries
- Data visualization packages
