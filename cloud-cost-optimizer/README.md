# Cloud Cost Optimizer

A Python library for analyzing and optimizing cloud resource costs across multiple cloud providers (AWS, Azure, GCP). This service helps organizations identify cost-saving opportunities and provides actionable recommendations.

## Features

- **Multi-Cloud Support**: Analyze resources across AWS, Azure, and GCP
- **Resource Analysis**: Collect and analyze resource utilization metrics
- **Cost Analysis**: Track and analyze resource costs across providers
- **Optimization Recommendations**: Generate actionable cost-saving recommendations
- **Policy Management**: Define and enforce cost optimization policies
- **Automated Optimization**: Apply recommendations automatically based on policies
- **Compliance Checks**: Ensure optimizations meet compliance requirements
- **Detailed Reporting**: Generate comprehensive cost optimization reports
- **Type Safety**: Full type hints and Pydantic models for reliable data handling
- **Extensible**: Easy to add support for additional cloud providers

## Installation

```bash
pip install cloud-cost-optimizer
```

## Requirements

- Python 3.9+
- Dependencies:
  - pydantic>=2.0.0
  - boto3>=1.26.0  # For AWS
  - azure-mgmt-network>=19.0.0  # For Azure
  - azure-identity>=1.12.0  # For Azure authentication
  - google-cloud-compute>=2.0.0  # For GCP
  - google-auth>=2.0.0  # For GCP authentication
  - rich>=13.0.0  # For output formatting
  - aiohttp>=3.8.0  # For async HTTP requests
  - asyncio>=3.4.3  # For async operations

## Quick Start

```python
from cloud_cost_optimizer import CloudCostOptimizer
from cloud_cost_optimizer.models import CloudProvider, OptimizationType

# Initialize optimizer with cloud credentials
optimizer = CloudCostOptimizer(
    aws_credentials={
        "aws_access_key_id": "your-key",
        "aws_secret_access_key": "your-secret",
        "region": "us-east-1"
    },
    azure_credentials={
        "subscription_id": "your-sub",
        "tenant_id": "your-tenant",
        "client_id": "your-client",
        "client_secret": "your-secret"
    }
)

# Analyze resources
analyses = await optimizer.analyze_resources(
    providers=[CloudProvider.AWS, CloudProvider.AZURE],
    include_metrics=True,
    include_costs=True
)

# Generate recommendations
recommendations = await optimizer.generate_recommendations(
    analyses=analyses,
    optimization_types=[
        OptimizationType.RIGHTSIZING,
        OptimizationType.SCHEDULING
    ],
    min_savings_amount=Decimal("100.00"),
    min_savings_percentage=20.0
)

# Generate report
report = await optimizer.generate_report(
    analyses=analyses,
    recommendations=recommendations,
    applied_optimizations=[],
    time_period="last-30-days"
)

print(f"Total Resources Analyzed: {report.summary.total_resources_analyzed}")
print(f"Total Recommendations: {report.summary.total_recommendations}")
print(f"Total Potential Savings: ${report.summary.total_potential_savings.monthly_cost}")
```

## Usage Examples

### Resource Analysis

```python
# Analyze specific resource types
analyses = await optimizer.analyze_resources(
    resource_types=[
        ResourceType.COMPUTE,
        ResourceType.STORAGE
    ]
)

# Analyze specific resources
analyses = await optimizer.analyze_resources(
    resource_ids=[
        "i-1234567890abcdef0",
        "vol-1234567890abcdef0"
    ]
)
```

### Optimization Recommendations

```python
# Generate recommendations with filters
recommendations = await optimizer.generate_recommendations(
    analyses=analyses,
    optimization_types=[OptimizationType.RIGHTSIZING],
    min_savings_amount=Decimal("50.00"),
    min_savings_percentage=15.0
)

# Apply recommendation
result = await optimizer.apply_recommendation(
    recommendation=recommendations[0],
    dry_run=True  # Simulate first
)
```

### Policy Management

```python
# Create optimization policy
policy = OptimizationPolicy(
    id="policy-123",
    name="Dev Environment Cost Optimization",
    description="Automatically optimize development resources",
    resource_types={ResourceType.COMPUTE, ResourceType.STORAGE},
    providers={CloudProvider.AWS, CloudProvider.AZURE},
    optimization_types={
        OptimizationType.RIGHTSIZING,
        OptimizationType.SCHEDULING
    },
    auto_approve=True,
    approval_required_above=Decimal("1000.00"),
    schedule="0 0 * * *"  # Daily at midnight
)

# Validate policy
is_valid, errors = await optimizer.validate_policy(policy)
if is_valid:
    print("Policy is valid")
else:
    print("Validation errors:", errors)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-cost-optimizer.git
cd cloud-cost-optimizer

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
pytest tests/test_optimizer.py
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

## Adding Support for New Cloud Providers

1. Add provider enum value:
   ```python
   class CloudProvider(str, Enum):
       NEW_PROVIDER = "new_provider"
   ```

2. Implement provider client:
   ```python
   class NewProviderClient:
       async def get_resources(self, resource_ids, resource_types):
           # Implement resource retrieval
           pass

       async def get_metrics(self, resource_id):
           # Implement metrics collection
           pass

       async def get_cost(self, resource_id):
           # Implement cost retrieval
           pass
   ```

3. Update optimizer initialization:
   ```python
   if new_provider_credentials:
       self.new_provider_client = NewProviderClient(**new_provider_credentials)
       self.providers.add(CloudProvider.NEW_PROVIDER)
   ```

4. Add provider-specific logic in optimizer methods.

5. Add tests for the new provider:
   ```python
   def test_new_provider_integration(optimizer):
       # Add integration tests
       pass
   ```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
