# Terraform Cost Analyzer

A Python library for analyzing and estimating costs of cloud resources defined in Terraform plans. This service helps organizations understand the cost implications of their infrastructure changes before applying them.

## Features

- **Multi-Cloud Support**: Analyze costs for AWS, Azure, and GCP resources
- **Plan Analysis**: Parse and extract resource information from Terraform plans
- **Resource Mapping**: Map provider-specific resources to standardized categories
- **Cost Estimation**: Calculate estimated costs for planned infrastructure changes
- **Cost Comparison**: Compare costs across different cloud providers
- **Type Safety**: Full type hints and Pydantic models for reliable data handling
- **Extensible**: Easy to add support for additional resource types and providers

## Installation

```bash
pip install terraform-cost-analyzer
```

## Requirements

- Python 3.9+
- Dependencies:
  - pydantic>=2.0.0
  - boto3>=1.26.0  # For AWS pricing
  - azure-mgmt-consumption>=9.0.0  # For Azure pricing
  - google-cloud-billing>=1.9.0  # For GCP pricing
  - rich>=13.0.0  # For output formatting

## Quick Start

```python
from terraform_cost_analyzer import TerraformCostAnalyzer

# Initialize analyzer
analyzer = TerraformCostAnalyzer()

# Analyze Terraform plan
analysis = analyzer.analyze_plan("terraform-plan.json")

# Print cost summary
print(f"Total Resources: {analysis.summary.total_resources}")
print(f"Resources to Add: {analysis.summary.resources_to_add}")
print(f"Resources to Update: {analysis.summary.resources_to_update}")
print(f"Resources to Delete: {analysis.summary.resources_to_delete}")
print(f"Estimated Monthly Cost: ${analysis.summary.total_monthly_cost:.2f}")

# Print cost breakdown
print("\nCost Breakdown:")
for resource_type, cost in analysis.summary.breakdown.dict().items():
    if cost > 0:
        print(f"{resource_type}: ${cost:.2f}")

# Print detailed resource costs
print("\nDetailed Resource Costs:")
for resource in analysis.resources:
    print(f"\n{resource.metadata.type} ({resource.metadata.name}):")
    print(f"  Provider: {resource.metadata.provider}")
    print(f"  Region: {resource.metadata.region}")
    print(f"  Action: {resource.action}")
    print(f"  Monthly Cost: ${resource.monthly_cost:.2f}")
```

## Usage Examples

### Basic Plan Analysis

```python
from terraform_cost_analyzer import TerraformCostAnalyzer
from terraform_cost_analyzer.models import CloudProvider

# Initialize with specific providers
analyzer = TerraformCostAnalyzer(
    providers=[CloudProvider.AWS, CloudProvider.AZURE]
)

# Analyze plan with custom options
analysis = analyzer.analyze_plan(
    plan_file="terraform-plan.json",
    include_previous_costs=True,
    currency="USD"
)

# Access results
for module in analysis.modules:
    print(f"\nModule: {module.name}")
    print(f"Monthly Cost: ${module.monthly_cost:.2f}")
    if module.cost_change:
        print(f"Cost Change: ${module.cost_change:+.2f}")
```

### Cost Comparison

```python
from terraform_cost_analyzer import TerraformCostAnalyzer

analyzer = TerraformCostAnalyzer()

# Compare costs across regions
comparison = analyzer.compare_regions(
    plan_file="terraform-plan.json",
    target_regions=[
        "us-east-1",
        "eu-west-1",
        "ap-southeast-1"
    ]
)

# Print comparison results
for region, costs in comparison.items():
    print(f"\nRegion: {region}")
    print(f"Total Monthly Cost: ${costs.total_monthly_cost:.2f}")
    print("Breakdown:")
    for service, cost in costs.breakdown.items():
        print(f"  {service}: ${cost:.2f}")
```

### Resource Mapping

```python
from terraform_cost_analyzer.parser import TerraformPlanParser
from terraform_cost_analyzer.models import ResourceType

parser = TerraformPlanParser()

# Parse plan and extract resources
with open("terraform-plan.json") as f:
    plan_data = parser.parse_plan_file(f)

# Extract and analyze resources
resources = parser.extract_resources(plan_data)
for metadata, action in resources:
    print(f"\nResource: {metadata.name}")
    print(f"Type: {metadata.type}")
    print(f"Normalized Type: {metadata.normalized_type}")
    print(f"Action: {action}")
    print("Specifications:")
    for key, value in metadata.specifications.items():
        print(f"  {key}: {value}")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/terraform-cost-analyzer.git
cd terraform-cost-analyzer

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
pytest tests/test_parser.py
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

## Adding Support for New Resource Types

1. Add resource type mapping in `parser.py`:
   ```python
   self._resource_mappings[CloudProvider.AWS].update({
       "aws_new_resource": ResourceType.COMPUTE,
   })
   ```

2. Add pricing logic in the appropriate provider client:
   ```python
   async def get_new_resource_price(
       self,
       resource_type: str,
       specifications: Dict[str, Any],
       region: str
   ) -> Decimal:
       # Implement pricing logic
       pass
   ```

3. Add tests for the new resource type:
   ```python
   def test_new_resource_parsing(parser):
       plan_data = {
           "resource_changes": [{
               "address": "aws_new_resource.example",
               "type": "aws_new_resource",
               # Add test data
           }]
       }
       resources = parser.extract_resources(plan_data)
       # Add assertions
   ```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
