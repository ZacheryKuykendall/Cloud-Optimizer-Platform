# AWS-GCP VPN Module

This module provides functionality for establishing and managing Site-to-Site VPN connections between AWS Virtual Private Gateways and Google Cloud VPN Gateways.

## Features

- Create and manage VPN connections between AWS VPCs and GCP VPCs
- Support for route-based VPNs
- BGP routing support with custom ASN configuration
- Dual-tunnel configuration for high availability
- Automatic cleanup of resources on failure
- Comprehensive error handling and status monitoring

## Components

### Data Models (`models.py`)

- `VpnConnection`: Represents a VPN connection between AWS and GCP
- `AwsVpnGateway`: AWS Virtual Private Gateway configuration
- `GcpVpnGateway`: Google Cloud VPN Gateway configuration
- `TunnelConfig`: VPN tunnel configuration
- `BgpConfig`: BGP routing configuration
- `RouteEntry`: VPN route entry

### Error Handling (`exceptions.py`)

- Provider-specific errors (AWS/GCP)
- Gateway-related errors
- Connection-related errors
- Validation errors
- Monitoring errors

### AWS Client (`aws_client.py`)

- Manage AWS Virtual Private Gateways
- Manage Customer Gateways
- Create and configure VPN connections
- Handle AWS-specific error cases

### GCP Client (`gcp_client.py`)

- Manage GCP VPN Gateways
- Manage VPN Tunnels
- Create and configure Cloud Routers
- Handle GCP-specific error cases

### VPN Manager (`manager.py`)

High-level interface for:
- Creating VPN connections
- Deleting VPN connections
- Retrieving connection status
- Managing connection lifecycle

## Usage

### Basic Setup

```python
from cloud_network_manager.vpn_modules.aws_gcp import (
    AwsVpnClient,
    GcpVpnClient,
    AwsGcpVpnManager,
    TunnelConfig,
)

# Initialize AWS client
aws_client = AwsVpnClient(
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    region="us-west-2"
)

# Initialize GCP client
gcp_client = GcpVpnClient(
    project_id="your-project-id",
    credentials_path="/path/to/credentials.json"  # or use credentials_dict
)

# Initialize manager
vpn_manager = AwsGcpVpnManager(
    aws_client=aws_client,
    gcp_client=gcp_client
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
    aws_vpc_id="vpc-12345678",
    aws_region="us-west-2",
    gcp_network="prod-vpc",
    gcp_region="us-west2",
    tunnels=tunnels,
    enable_bgp=True,
    aws_asn=65001,
    gcp_asn=65002,
    labels={
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
    connection_id="aws-id:gcp-id",
    gcp_region="us-west2"
)

print(f"Connection status: {connection.status}")
print(f"BGP enabled: {connection.bgp_config.enabled if connection.bgp_config else False}")

# Delete connection
await vpn_manager.delete_vpn_connection(
    connection_id="aws-id:gcp-id",
    aws_vpc_id="vpc-12345678",
    gcp_region="us-west2"
)
```

## Error Handling

The module provides comprehensive error handling:

```python
from cloud_network_manager.vpn_modules.aws_gcp.exceptions import (
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
   - Use appropriate gateway types for production workloads

2. **Security**
   - Use strong pre-shared keys
   - Regularly rotate credentials
   - Implement proper security groups/firewall rules

3. **Monitoring**
   - Monitor tunnel status regularly
   - Set up alerts for tunnel down events
   - Track BGP route propagation

4. **Cost Management**
   - Be aware of data transfer costs
   - Choose appropriate gateway types
   - Clean up unused resources

## Limitations

1. AWS VPN Gateway provisioning can take 5-10 minutes
2. Maximum throughput depends on gateway type
3. BGP ASNs must be unique across your network
4. Some features require specific gateway generations
5. GCP requires route-based VPNs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This module is part of the Cloud Network Manager package and is licensed under the MIT License.
