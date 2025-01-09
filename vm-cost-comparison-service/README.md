# VM Cost Comparison Service

A service for comparing virtual machine costs across different cloud providers (AWS, Azure, GCP). This service helps users find the most cost-effective VM options that meet their requirements by analyzing pricing across providers, regions, and purchase options.

## Features

- Compare VM costs across AWS, Azure, and Google Cloud
- Support for different operating systems (Linux, Windows, RHEL, SUSE, Ubuntu)
- Multiple purchase options (On-Demand, Reserved, Spot)
- GPU and specialized hardware support
- Comprehensive cost breakdown including compute and storage
- Filtering by CPU, memory, features, and certifications
- Cost optimization recommendations
- Currency normalization across providers

## Architecture

### Core Components

- **Comparison Engine**: Orchestrates the comparison process and aggregates results
- **Provider Clients**: Interface with cloud provider APIs for instance types and pricing
- **Cost Models**: Standardized representation of VM costs and requirements
- **Currency Converter**: Normalizes costs across different currencies

### Cloud Provider Integration

- **AWS**: Uses EC2 and Pricing APIs
- **Azure**: Uses Compute Management and Commerce APIs
- **GCP**: Uses Compute Engine and Cloud Billing APIs

## Installation

```bash
pip install vm-cost-comparison-service
```

## Usage

### Basic Comparison

```python
from vm_comparison import (
    VmComparisonEngine,
    VmRequirements,
    VmSize,
    OperatingSystem,
    PurchaseOption,
)

# Initialize providers
aws_provider = AwsVmProvider(
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    region="us-west-2"
)

azure_provider = AzureVmProvider(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    subscription_id="your-subscription-id",
    location="westus2"
)

gcp_provider = GcpVmProvider(
    project_id="your-project-id",
    credentials_path="/path/to/credentials.json",
    region="us-central1"
)

# Initialize comparison engine
engine = VmComparisonEngine(
    aws_provider=aws_provider,
    azure_provider=azure_provider,
    gcp_provider=gcp_provider,
    currency_converter=currency_converter
)

# Define requirements
requirements = VmRequirements(
    size=VmSize(
        vcpus=4,
        memory_gb=16,
        gpu_count=0
    ),
    operating_system=OperatingSystem.LINUX,
    purchase_option=PurchaseOption.ON_DEMAND,
    region="us-west"
)

# Compare VMs
result = await engine.compare_vms(requirements)

# Print results
print(f"Total options considered: {result.total_options_considered}")
print(f"Filtered options: {result.filtered_options_count}")
print(f"\nRecommended option:")
print(f"Provider: {result.comparison.recommended_option.provider}")
print(f"Instance type: {result.comparison.recommended_option.instance_type}")
print(f"Monthly cost: ${result.comparison.recommended_option.monthly_cost}")

print("\nAll options:")
for estimate in result.comparison.estimates:
    print(f"\nProvider: {estimate.provider}")
    print(f"Instance type: {estimate.instance_type}")
    print(f"Monthly cost: ${estimate.monthly_cost}")
    print("Cost components:")
    for component in estimate.cost_components:
        print(f"  {component.name}: ${component.monthly_cost}")
```

### Filtering Results

```python
from vm_comparison import ComparisonFilter

# Create filter
filter = ComparisonFilter(
    providers={CloudProvider.AWS, CloudProvider.AZURE},
    min_vcpus=2,
    max_vcpus=8,
    min_memory_gb=4,
    max_memory_gb=32,
    required_features={"gpu", "nvme"},
    max_monthly_cost=Decimal("500.00")
)

# Compare with filter
result = await engine.compare_vms(requirements, filter)
```

## Cost Components

The service breaks down costs into components:

- **Compute**: Base instance cost
- **Storage**: Attached disk costs
- **OS License**: Operating system licensing costs
- **Support**: Support plan costs (if applicable)

## Best Practices

1. **Region Selection**
   - Choose comparable regions across providers
   - Consider data transfer costs between regions
   - Be aware of feature availability in different regions

2. **Purchase Options**
   - Use On-Demand for variable workloads
   - Consider Reserved instances for stable, long-running workloads
   - Evaluate Spot instances for fault-tolerant, interruptible workloads

3. **Cost Optimization**
   - Start with basic requirements and add constraints as needed
   - Consider the trade-offs between different instance families
   - Factor in additional costs like data transfer and storage

4. **Performance Considerations**
   - CPU architectures vary across providers
   - Memory bandwidth and IOPS can vary significantly
   - Network performance varies by instance type and region

## Error Handling

The service provides detailed error information:

```python
from vm_comparison.exceptions import (
    ValidationError,
    PricingError,
    ProviderError,
)

try:
    result = await engine.compare_vms(requirements)
except ValidationError as e:
    print(f"Invalid requirements: {e}")
    print(f"Field: {e.field}")
    print(f"Constraints: {e.constraints}")
except PricingError as e:
    print(f"Pricing error: {e}")
    print(f"Provider: {e.provider}")
    print(f"Region: {e.region}")
except ProviderError as e:
    print(f"Provider error: {e}")
    print(f"Details: {e.details}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
