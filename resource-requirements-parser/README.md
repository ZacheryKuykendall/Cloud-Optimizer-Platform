# Resource Requirements Parser

A Python library for parsing infrastructure requirements from various sources like Terraform and CloudFormation. This library helps extract standardized resource specifications from infrastructure-as-code definitions, making it easier to analyze, compare, and optimize cloud resource usage.

## Features

- Parse infrastructure requirements from multiple sources:
  - Terraform configurations (.tf files)
  - AWS CloudFormation templates (YAML/JSON)
  - More sources coming soon (ARM templates, Kubernetes manifests)

- Extract detailed resource specifications for:
  - Compute resources (VMs, containers, serverless functions)
  - Storage resources (block storage, object storage, file systems)
  - Network resources (VPCs, subnets, security groups)
  - Database resources (relational, NoSQL, caches)

- Standardized output format:
  - Consistent resource type categorization
  - Normalized resource specifications
  - Dependency tracking between resources
  - Resource tags and metadata

- Validation and error handling:
  - Input validation for source files
  - Resource specification validation
  - Detailed error messages and warnings
  - Dependency cycle detection

## Installation

You can install the package using pip:

```bash
pip install resource-requirements-parser
```

For development installation with additional tools:

```bash
pip install resource-requirements-parser[dev]
```

## Quick Start

Here's a simple example of parsing a Terraform configuration:

```python
from resource_requirements_parser import parse_requirements, SourceType

# Parse Terraform configuration
result = parse_requirements("path/to/terraform/files", SourceType.TERRAFORM)

# Print found resources
print(f"Found {len(result.requirements.resources)} resources:")
for resource in result.requirements.resources:
    print(f"- {resource.name} ({resource.type.value})")

# Check for any warnings
for warning in result.warnings:
    print(f"Warning: {warning}")
```

Parsing a CloudFormation template:

```python
from resource_requirements_parser import parse_requirements, SourceType

# Parse CloudFormation template
result = parse_requirements("template.yaml", SourceType.CLOUDFORMATION)

# Get compute resources
compute_resources = result.requirements.get_resources_by_type(ResourceType.COMPUTE)
for resource in compute_resources:
    print(f"Compute resource: {resource.name}")
    print(f"  Type: {resource.compute.type}")
    print(f"  vCPUs: {resource.compute.vcpus}")
    print(f"  Memory: {resource.compute.memory_gb} GB")
```

## Detailed Usage

### Resource Types

The library categorizes resources into several types:

```python
from resource_requirements_parser import ResourceType

# Available resource types
RESOURCE_TYPES = [
    ResourceType.COMPUTE,     # VMs, containers, functions
    ResourceType.STORAGE,     # Disks, buckets, file systems
    ResourceType.NETWORK,     # VPCs, subnets, security groups
    ResourceType.DATABASE,    # RDS, DynamoDB, Redis
    ResourceType.CONTAINER,   # ECS, Kubernetes
    ResourceType.SERVERLESS,  # Lambda, Cloud Functions
    ResourceType.CACHE,       # ElastiCache, Memcached
    ResourceType.QUEUE,       # SQS, Pub/Sub
    ResourceType.DNS,         # Route53, Cloud DNS
    ResourceType.CDN,         # CloudFront, Cloud CDN
    ResourceType.MONITORING,  # CloudWatch, Stackdriver
    ResourceType.SECURITY,    # IAM, KMS, Security Center
]
```

### Resource Requirements

Each resource type has specific requirements that can be extracted:

```python
# Compute requirements
compute_resource = result.requirements.get_resource_by_name("aws_instance.web")
if compute_resource and compute_resource.compute:
    print(f"Instance type: {compute_resource.compute.instance_type}")
    print(f"vCPUs: {compute_resource.compute.vcpus}")
    print(f"Memory: {compute_resource.compute.memory_gb} GB")
    print(f"Operating system: {compute_resource.compute.operating_system}")

# Storage requirements
storage_resource = result.requirements.get_resource_by_name("aws_ebs_volume.data")
if storage_resource and storage_resource.storage:
    print(f"Capacity: {storage_resource.storage.capacity_gb} GB")
    print(f"IOPS: {storage_resource.storage.iops}")
    print(f"Encrypted: {storage_resource.storage.encryption_required}")
```

### Dependencies

You can analyze resource dependencies:

```python
# Get dependencies for a resource
resource = result.requirements.get_resource_by_name("aws_instance.web")
if resource:
    # Resources this depends on
    dependencies = result.requirements.get_dependencies(resource.name)
    print("Dependencies:", [dep.name for dep in dependencies])
    
    # Resources that depend on this
    dependents = result.requirements.get_dependent_resources(resource.name)
    print("Dependent resources:", [dep.name for dep in dependents])
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to:

- Report bugs
- Request features
- Submit pull requests
- Add support for new source types
- Improve documentation

## Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resource-requirements-parser.git
cd resource-requirements-parser
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install development dependencies:
```bash
pip install -e ".[dev,test]"
```

4. Run tests:
```bash
pytest
```

5. Run linting and type checking:
```bash
black .
isort .
mypy src/resource_requirements_parser
pylint src/resource_requirements_parser
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
