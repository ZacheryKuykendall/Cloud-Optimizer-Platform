# Azure-GCP VPN Module

This module provides functionality for establishing and managing Site-to-Site VPN connections between Azure Virtual Network Gateways and Google Cloud VPN Gateways.

## Features

- Create and manage VPN connections between Azure VNets and GCP VPCs
- Support for route-based VPNs (required by GCP)
- BGP routing support with custom ASN configuration
- Dual-tunnel configuration for high availability
- Automatic cleanup of resources on failure
- Comprehensive error handling and status monitoring

## Components

### Data Models (`models.py`)

- `VpnConnection`: Represents a VPN connection between Azure and GCP
- `AzureVNetGateway`: Azure Virtual Network Gateway configuration
- `GcpVpnGateway`: Google Cloud VPN Gateway configuration
- `TunnelConfig`: VPN tunnel configuration
- `BgpConfig`: BGP routing configuration
- `RouteEntry`: VPN route entry

### Error Handling (`exceptions.py`)

- Provider-specific errors (Azure/GCP)
- Gateway-related errors
- Connection-related errors
- Validation errors
- Monitoring errors

### Azure Client (`azure_client.py`)

- Manage Azure Virtual Network Gateways
- Manage Local Network Gateways
- Create and configure VPN connections
- Handle Azure-specific error cases

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
from cloud_network_manager.vpn_modules.azure_gcp import (
    AzureVpnClient,
    GcpVpnClient,
    AzureGcpVpnManager,
    TunnelConfig,
)

# Initialize Azure client
azure_client = AzureVpnClient(
    subscription_id="your-subscription-id",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Initialize GCP client
gcp_client = GcpVpnClient(
    project_id="your-project-id",
    credentials_path="/path/to/credentials.json"  # or use credentials_dict
)

# Initialize manager
vpn_manager = AzureGcpVpnManager(
    azure_client=azure_client,
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
    azure_resource_group="prod-rg",
    azure_vnet_name="prod-vnet",
    azure_location="westus2",
    gcp_network="prod-vpc",
    gcp_region="us-west2",
    tunnels=tunnels,
    enable_bgp=True,
    azure_asn=65001,
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
    connection_id="azure-id:gcp-id",
    azure_resource_group="prod-rg",
    gcp_region="us-west2"
)

print(f"Connection status: {connection.status}")
print(f"BGP enabled: {connection.bgp_config.enabled if connection.bgp_config else False}")

# Delete connection
await vpn_manager.delete_vpn_connection(
    connection_id="azure-id:gcp-id",
    azure_resource_group="prod-rg",
    gcp_region="us-west2"
)
```

## Error Handling

The module provides comprehensive error handling:

```python
from cloud_network_manager.vpn_modules.azure_gcp.exceptions import (
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
   - Implement proper network security groups/firewall rules

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
2. Maximum throughput depends on gateway SKU/tier
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
