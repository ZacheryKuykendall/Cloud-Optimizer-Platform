# Resource Identification Service

A Python service for identifying and classifying cloud resources across different providers. This service provides a robust platform for discovering, analyzing, and managing cloud resources with support for dependency analysis and automatic classification.

## Features

- Multi-Cloud Resource Discovery:
  - AWS resource scanning
  - Azure resource scanning
  - GCP resource scanning
  - Support for other providers
  - Parallel scanning

- Resource Classification:
  - Automatic classification rules
  - Custom classification logic
  - Machine learning classification
  - Resource tagging
  - Resource labeling

- Dependency Analysis:
  - Resource dependency discovery
  - Dependency graph generation
  - Impact analysis
  - Critical path identification
  - Graph visualization

- Resource Monitoring:
  - Resource metrics collection
  - Usage tracking
  - Status monitoring
  - Performance analysis
  - Health checks

- Advanced Features:
  - Resource caching
  - Rate limiting
  - Retry handling
  - Concurrent operations
  - Batch processing

## Installation

```bash
pip install resource-identification-service
```

## Prerequisites

- Python 3.8 or higher
- Cloud provider credentials:
  - AWS credentials
  - Azure credentials
  - GCP credentials
- PostgreSQL (optional, for persistent storage)
- Redis (optional, for caching)

## Quick Start

### Basic Usage

```python
from resource_identification import (
    ResourceScanConfig,
    CloudProvider,
    ResourceType
)

# Configure resource scan
config = ResourceScanConfig(
    providers=[CloudProvider.AWS, CloudProvider.AZURE],
    regions=["us-east-1", "eastus"],
    resource_types=[
        ResourceType.COMPUTE,
        ResourceType.STORAGE
    ]
)

# Perform scan
scanner = ResourceScanner(config)
result = scanner.scan()

# Process results
for resource in result.resources:
    print(f"Found {resource.type} resource: {resource.name}")
    print(f"Provider: {resource.provider}")
    print(f"Status: {resource.status}")
```

### Resource Classification

```python
from resource_identification import (
    ResourceClassificationRule,
    ResourceClassification
)

# Create classification rule
rule = ResourceClassificationRule(
    name="Production Database Rule",
    provider=CloudProvider.AWS,
    resource_type=ResourceType.DATABASE,
    conditions=[
        {"tag:Environment": "production"},
        {"instance_class": "db.r5.large"}
    ],
    classification=ResourceClassification.CRITICAL
)

# Apply classification
classifier = ResourceClassifier([rule])
classified_resources = classifier.classify(resources)
```

### Dependency Analysis

```python
from resource_identification import ResourceDependencyGraph

# Create dependency graph
graph = ResourceDependencyGraph(
    resources=resources,
    dependencies=dependencies
)

# Analyze dependencies
analyzer = DependencyAnalyzer(graph)
critical_paths = analyzer.find_critical_paths()
impact_analysis = analyzer.analyze_impact("resource-id")
```

### Resource Monitoring

```python
from resource_identification import ResourceUsage

# Get resource metrics
monitor = ResourceMonitor()
usage = monitor.get_resource_usage("resource-id")

print(f"CPU Utilization: {usage.cpu_utilization}%")
print(f"Memory Utilization: {usage.memory_utilization}%")
print(f"Network In/Out: {usage.network_in}/{usage.network_out} MB/s")
```

## Advanced Usage

### Custom Provider Integration

```python
from resource_identification import CloudProvider

class CustomProvider:
    def scan_resources(self, config: ResourceScanConfig) -> List[CloudResource]:
        # Implement custom scanning logic
        pass

# Register custom provider
scanner.register_provider(
    CloudProvider.OTHER,
    CustomProvider()
)
```

### Batch Operations

```python
# Configure batch scan
batch_config = ResourceScanConfig(
    providers=[CloudProvider.AWS],
    regions=["us-east-1", "us-west-2"],
    parallel_scans=5
)

# Execute batch scan
batch_result = scanner.scan_batch(batch_config)

# Process batch results
for result in batch_result.results:
    print(f"Scanned region: {result.region}")
    print(f"Found resources: {len(result.resources)}")
```

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resource-identification-service.git
cd resource-identification-service
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
pytest tests/test_scanner.py
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
- [Cloud Resource Inventory](https://github.com/yourusername/cloud-resource-inventory)

## Acknowledgments

- AWS SDK for Python (Boto3)
- Azure SDK for Python
- Google Cloud SDK for Python
- NetworkX for graph analysis
- scikit-learn for classification
