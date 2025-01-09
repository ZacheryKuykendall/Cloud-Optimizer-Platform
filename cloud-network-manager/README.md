# Cloud Network Manager

A Python library for managing cloud networks and VPN connections across multiple cloud providers (AWS, Azure, GCP). This service helps organizations establish and maintain secure network connectivity between different cloud environments.

## Features

- **Multi-Cloud Support**: Manage networks across AWS, Azure, and GCP
- **VPN Management**: Create and manage VPN connections between different cloud providers
- **Network Validation**: Validate network configurations before deployment
- **State Management**: Track and monitor network resources and their states
- **Security Controls**: Manage network ACLs, security groups, and routing tables
- **Monitoring**: Track network metrics and VPN tunnel status
- **Type Safety**: Full type hints and Pydantic models for reliable data handling
- **Extensible**: Easy to add support for additional cloud providers

## Installation

```bash
pip install cloud-network-manager
```

## Requirements

- Python 3.9+
- Dependencies:
  - pydantic>=2.0.0
  - boto3>=1.26.0  # For AWS
  - azure-mgmt-network>=19.0.0  # For Azure
  - google-cloud-compute>=2.0.0  # For GCP
  - rich>=13.0.0  # For output formatting

## Quick Start

```python
from cloud_network_manager import CloudNetworkManager
from cloud_network_manager.models import (
    CloudProvider,
    NetworkConfiguration,
    VPNGatewayConfiguration,
    VPNTunnelConfiguration,
)
from ipaddress import IPv4Network

# Initialize manager with cloud credentials
manager = CloudNetworkManager(
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

# Create networks in different clouds
aws_network = await manager.create_network(
    NetworkConfiguration(
        provider=CloudProvider.AWS,
        network_type="vpc",
        name="aws-network",
        region="us-east-1",
        cidr_block=IPv4Network("10.0.0.0/16"),
        subnets=[
            IPv4Network("10.0.1.0/24"),
            IPv4Network("10.0.2.0/24")
        ]
    )
)

azure_network = await manager.create_network(
    NetworkConfiguration(
        provider=CloudProvider.AZURE,
        network_type="vnet",
        name="azure-network",
        region="eastus",
        cidr_block=IPv4Network("172.16.0.0/16"),
        subnets=[
            IPv4Network("172.16.1.0/24"),
            IPv4Network("172.16.2.0/24")
        ]
    )
)

# Create VPN connection between networks
vpn = await manager.create_vpn_connection(
    source_network=aws_network,
    target_network=azure_network,
    source_gateway=VPNGatewayConfiguration(
        name="aws-gateway",
        type="site_to_site",
        bandwidth="1Gbps",
        availability_zones=["us-east-1a"]
    ),
    target_gateway=VPNGatewayConfiguration(
        name="azure-gateway",
        type="route_based",
        bandwidth="1Gbps"
    ),
    tunnels=[
        VPNTunnelConfiguration(
            name="tunnel-1",
            inside_cidr=IPv4Network("169.254.1.0/30")
        )
    ]
)

# Get current network state
state = await manager.get_network_state()
print(f"Total Networks: {len(state.networks)}")
print(f"Total VPN Connections: {len(state.vpn_connections)}")
```

## Usage Examples

### Network Management

```python
from cloud_network_manager import CloudNetworkManager
from cloud_network_manager.models import CloudProvider, NetworkConfiguration

# Initialize manager
manager = CloudNetworkManager(aws_credentials={...})

# Create network
network = await manager.create_network(
    NetworkConfiguration(
        provider=CloudProvider.AWS,
        network_type="vpc",
        name="production-vpc",
        region="us-east-1",
        cidr_block=IPv4Network("10.0.0.0/16")
    )
)

# Delete network
await manager.delete_network(
    provider=CloudProvider.AWS,
    network_id=network.id
)
```

### VPN Management

```python
# Create VPN connection
vpn = await manager.create_vpn_connection(
    source_network=aws_network,
    target_network=azure_network,
    source_gateway=aws_gateway_config,
    target_gateway=azure_gateway_config,
    tunnels=tunnel_configs
)

# Delete VPN connection
await manager.delete_vpn_connection(
    connection_id=vpn.id,
    source_provider=CloudProvider.AWS,
    target_provider=CloudProvider.AZURE
)
```

### Network Validation

```python
# Validate network configuration
validation = await manager.validate_network_config(network_config)
if not validation.valid:
    print("Validation errors:")
    for error in validation.errors:
        print(f"- {error.description} (Severity: {error.severity})")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-network-manager.git
cd cloud-network-manager

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
pytest tests/test_manager.py
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

1. Create a new VPN module in `src/cloud_network_manager/vpn_modules/`:
   ```python
   class NewProviderVPNManager:
       async def create_network(self, config: NetworkConfiguration) -> str:
           # Implement network creation
           pass

       async def delete_network(self, network_id: str) -> None:
           # Implement network deletion
           pass

       # Implement other required methods
   ```

2. Update the provider mappings in `CloudNetworkManager`:
   ```python
   self.vpn_managers[(CloudProvider.AWS, CloudProvider.NEW)] = NewProviderVPNManager(
       aws_credentials=aws_credentials,
       new_provider_credentials=new_credentials
   )
   ```

3. Add tests for the new provider:
   ```python
   def test_new_provider_integration(manager):
       # Add integration tests
       pass
   ```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
