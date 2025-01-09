# AWS-Azure VPN Module

This module provides functionality for establishing and managing Site-to-Site VPN connections between AWS Virtual Private Gateways and Azure Virtual Network Gateways.

## Features

- Create and manage VPN connections between AWS VPCs and Azure VNets
- Support for both policy-based and route-based VPNs
- BGP routing support with custom ASN configuration
- Dual-tunnel configuration for high availability
- Automatic cleanup of resources on failure
- Comprehensive error handling and status monitoring

## Components

### Data Models (`models.py`)

- `VpnConnection`: Represents a VPN connection between AWS and Azure
- `AwsVpnGateway`: AWS Virtual Private Gateway configuration
- `AzureVNetGateway`: Azure Virtual Network Gateway configuration
- `TunnelConfig`: VPN tunnel configuration
- `BgpConfig`: BGP routing configuration
- `RouteEntry`: VPN route entry

### Error Handling (`exceptions.py`)

- Provider-specific errors (AWS/Azure)
- Gateway-related errors
- Connection-related errors
- Validation errors
- Monitoring errors

### AWS Client (`aws_client.py`)

- Manage AWS Virtual Private Gateways
- Manage Customer Gateways
- Create and configure VPN connections
- Handle AWS-specific error cases

### Azure Client (`azure_client.py`)

- Manage Azure Virtual Network Gateways
- Manage Local Network Gateways
- Create and configure VPN connections
- Handle Azure-specific error cases

### VPN Manager (`manager.py`)

High-level interface for:
- Creating VPN connections
- Deleting VPN connections
- Retrieving connection status
- Managing connection lifecycle

## Usage

### Basic Setup

```python
from cloud_network_manager.vpn_modules.aws_azure import (
    AwsVpnClient,
    AzureVpnClient,
    AwsAzureVpnManager,
    TunnelConfig,
)

# Initialize clients
aws_client = AwsVpnClient(
    aws_access_key_id="your-aws-key",
    aws_secret_access_key="your-aws-secret",
    region="us-west-2"
)

azure_client = AzureVpnClient(
    subscription_id="your-subscription-id",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Initialize manager
vpn_manager = AwsAzureVpnManager(
    aws_client=aws_client,
    azure_client=azure_client
)
```

### Creating a VPN Connection

```python
# Configure tunnel settings
tunnels = [
    TunnelConfig(
        inside_cidr="169.254.0.0/30",
        preshared_key="your-psk-1"
    ),
    TunnelConfig(
        inside_cidr="169.254.0.4/30",
        preshared_key="your-psk-2"
    )
]

# Create VPN connection
connection = await vpn_manager.create_vpn_connection(
    name="prod-vpn",
    aws_vpc_id="vpc-12345",
    aws_region="us-west-2",
    azure_resource_group="prod-rg",
    azure_vnet_name="prod-vnet",
    azure_location="westus2",
    tunnels=tunnels,
    enable_bgp=True,
    aws_asn=65001,
    azure_asn=65002,
    tags={
        "environment": "production",
        "team": "networking"
    }
)

print(f"VPN Connection created: {connection.id}")
```

### Managing VPN Connections

```python
# Get connection details
connection = await vpn_manager.get_vpn_connection(
    connection_id="vpn-12345:my-vpn-connection",
    azure_resource_group="prod-rg"
)

print(f"Connection status: {connection.status}")
print(f"BGP enabled: {connection.bgp_config.enabled if connection.bgp_config else False}")

# Delete connection
await vpn_manager.delete_vpn_connection(
    connection_id="vpn-12345:my-vpn-connection",
    aws_vpc_id="vpc-12345",
    azure_resource_group="prod-rg"
)
```

## Error Handling

The module provides comprehensive error handling:

```python
from cloud_network_manager.vpn_modules.aws_azure.exceptions import (
    ValidationError,
    VpnConnectionCreationError,
    VpnConnectionNotFoundError,
)

try:
    connection = await vpn_manager.create_vpn_connection(...)
except ValidationError as e:
    print(f"Invalid configuration: {e}")
except VpnConnectionCreationError as e:
    print(f"Failed to create VPN: {e}")
    if e.details:
        print(f"Details: {e.details}")
```

## Best Practices

1. **High Availability**
   - Always configure two tunnels for redundancy
   - Enable BGP for dynamic routing when possible
   - Use appropriate gateway SKUs for production workloads

2. **Security**
   - Use strong pre-shared keys
   - Regularly rotate credentials
   - Implement proper network security groups/ACLs

3. **Monitoring**
   - Monitor tunnel status regularly
   - Set up alerts for tunnel down events
   - Track BGP route propagation

4. **Cost Management**
   - Be aware of data transfer costs
   - Choose appropriate gateway SKUs
   - Clean up unused resources

## Limitations

1. Azure VPN Gateway provisioning can take 30-45 minutes
2. Maximum throughput depends on gateway SKU
3. BGP ASNs must be unique across your network
4. Some features require specific gateway generations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This module is part of the Cloud Network Manager package and is licensed under the MIT License.
