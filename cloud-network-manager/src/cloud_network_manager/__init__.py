"""Cloud Network Manager

A Python library for managing cross-cloud network connectivity between AWS, Azure, and GCP.
This library provides functionality for creating and managing VPN connections,
routing, and network security across different cloud providers.
"""

from cloud_network_manager.models import (
    CloudProvider,
    VpnType,
    NetworkProtocol,
    IkeVersion,
    VpnStatus,
    NetworkAddress,
    IkeConfig,
    IpsecConfig,
    VpnTunnel,
    RouteEntry,
    NetworkAcl,
    VpnConnection,
    NetworkMonitoring,
    NetworkMetrics,
    TerraformConfig,
    NetworkOperation,
    HealthCheck,
    MaintenanceWindow,
)
from cloud_network_manager.exceptions import (
    CloudNetworkError,
    ProviderError,
    VpnError,
    NetworkValidationError,
    ConnectionError,
    TunnelError,
    RoutingError,
    NetworkAclError,
    MonitoringError,
    TerraformError,
    ConfigurationError,
    AuthenticationError,
    OperationError,
    HealthCheckError,
    MaintenanceWindowError,
    ResourceLimitError,
    NetworkConflictError,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "CloudProvider",
    "VpnType",
    "NetworkProtocol",
    "IkeVersion",
    "VpnStatus",
    "NetworkAddress",
    "IkeConfig",
    "IpsecConfig",
    "VpnTunnel",
    "RouteEntry",
    "NetworkAcl",
    "VpnConnection",
    "NetworkMonitoring",
    "NetworkMetrics",
    "TerraformConfig",
    "NetworkOperation",
    "HealthCheck",
    "MaintenanceWindow",

    # Exceptions
    "CloudNetworkError",
    "ProviderError",
    "VpnError",
    "NetworkValidationError",
    "ConnectionError",
    "TunnelError",
    "RoutingError",
    "NetworkAclError",
    "MonitoringError",
    "TerraformError",
    "ConfigurationError",
    "AuthenticationError",
    "OperationError",
    "HealthCheckError",
    "MaintenanceWindowError",
    "ResourceLimitError",
    "NetworkConflictError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
