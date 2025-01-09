# Cloud Resource Inventory

A Python library for tracking and managing cloud resources across multiple cloud providers (AWS, Azure, GCP). This service provides a centralized inventory system with support for resource discovery, tagging, grouping, and querying.

## Features

- **Multi-Cloud Support**: Track resources across AWS, Azure, and GCP
- **Resource Discovery**: Automatically discover cloud resources and their configurations
- **Resource Tracking**: Monitor resource status, lifecycle, and criticality
- **Resource Tagging**: Apply and manage tags for better resource organization
- **Resource Grouping**: Create logical groups of related resources
- **Resource Querying**: Search resources using flexible criteria
- **Inventory State**: Maintain current state of all tracked resources
- **Summary Statistics**: Generate resource usage and cost summaries
- **Type Safety**: Full type hints and Pydantic models for reliable data handling
- **Async Support**: Asynchronous operations for better performance
- **Extensible**: Easy to add support for additional cloud providers

## Installation

```bash
pip install cloud-resource-inventory
```

## Requirements

- Python 3.9+
- Dependencies:
  - pydantic>=2.0.0
  - boto3>=1.26.0  # For AWS
  - azure-mgmt-resource>=21.0.0  # For Azure
  - google-cloud-resource-manager>=1.0.0  # For GCP
  - aiohttp>=3.8.0  # For async operations
  - rich>=13.0.0  # For output formatting

## Quick Start

```python
from cloud_resource_inventory import ResourceInventoryManager
from cloud_resource_inventory.models import CloudProvider, ResourceType

# Initialize inventory manager
manager = ResourceInventoryManager(
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

# Discover resources
resources = await manager.discover_resources(
    providers=[CloudProvider.AWS, CloudProvider.AZURE],
    resource_types=[ResourceType.COMPUTE, ResourceType.STORAGE],
    include_metrics=True,
    include_costs=True
)

# Create resource group
group = await manager.create_group(
    name="production-resources",
    description="Production environment resources",
    tags={"env": "prod"}
)

# Add resources to group
await manager.add_to_group(
    group_id=group.id,
    resource_ids=[resource.id for resource in resources]
)

# Query resources
results = await manager.query_resources(
    ResourceQuery(
        providers=[CloudProvider.AWS],
        types=[ResourceType.COMPUTE],
        tags={"env": "prod"},
        statuses=["active"]
    )
)

# Print summary
print(f"Total Resources: {manager.state.summary.total_resources}")
print(f"Resources by Provider: {manager.state.summary.resources_by_provider}")
print(f"Total Cost (USD): {manager.state.summary.total_cost.get('USD', 0.0)}")
```

## Usage Examples

### Resource Discovery

```python
# Discover specific resource types
compute_resources = await manager.discover_resources(
    resource_types=[ResourceType.COMPUTE]
)

# Discover in specific regions
us_resources = await manager.discover_resources(
    regions=["us-east-1", "us-west-1"]
)

# Discover with metrics and costs
detailed_resources = await manager.discover_resources(
    include_metrics=True,
    include_costs=True
)
```

### Resource Tagging

```python
# Tag a resource
resource = await manager.tag_resource(
    resource_id="res-123",
    tags={
        "env": "prod",
        "team": "platform",
        "cost-center": "12345"
    }
)
```

### Resource Groups

```python
# Create group
group = await manager.create_group(
    name="database-resources",
    description="Database instances and storage",
    tags={"type": "database"}
)

# Add resources to group
await manager.add_to_group(
    group_id=group.id,
    resource_ids=["res-123", "res-456"]
)
```

### Resource Queries

```python
# Query by multiple criteria
resources = await manager.query_resources(
    ResourceQuery(
        providers=[CloudProvider.AWS],
        types=[ResourceType.COMPUTE],
        regions=["us-east-1"],
        statuses=["active"],
        lifecycles=["production"],
        criticalities=["high"],
        tags={"env": "prod"},
        created_after=datetime(2023, 1, 1)
    )
)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-resource-inventory.git
cd cloud-resource-inventory

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
pytest tests/test_inventory.py
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

2. Implement provider client initialization:
   ```python
   def _init_new_provider_client(self, credentials: Dict[str, str]) -> Any:
       # Initialize client for new provider
       pass
   ```

3. Implement provider-specific resource discovery:
   ```python
   async def _discover_provider_resources(
       self,
       provider: CloudProvider,
       resource_types: Optional[List[ResourceType]],
       regions: Optional[List[str]]
   ) -> List[Resource]:
       if provider == CloudProvider.NEW_PROVIDER:
           # Implement resource discovery for new provider
           pass
   ```

4. Add provider-specific resource operations:
   ```python
   async def _update_provider_resource(self, resource: Resource) -> None:
       if resource.provider == CloudProvider.NEW_PROVIDER:
           # Implement resource updates for new provider
           pass
   ```

5. Add tests for the new provider:
   ```python
   @pytest.mark.asyncio
   async def test_new_provider_integration():
       # Add integration tests
       pass
   ```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
