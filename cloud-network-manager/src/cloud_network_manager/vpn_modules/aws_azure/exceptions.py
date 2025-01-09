"""Custom exceptions for AWS-Azure VPN module.

This module defines exceptions specific to managing VPN connections
between AWS Virtual Private Gateways and Azure Virtual Network Gateways.
"""

from typing import Any, Dict, Optional


class VpnError(Exception):
    """Base exception for all VPN-related errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(VpnError):
    """Raised when VPN configuration validation fails."""

    def __init__(self, message: str, invalid_value: Any = None):
        super().__init__(message)
        self.invalid_value = invalid_value


class ProviderError(VpnError):
    """Base class for cloud provider-specific errors."""
    pass


class AwsError(ProviderError):
    """Base class for AWS-specific errors."""

    def __init__(
        self,
        message: str,
        aws_error_code: Optional[str] = None,
        aws_request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.aws_error_code = aws_error_code
        self.aws_request_id = aws_request_id
        self.details = details or {}


class AzureError(ProviderError):
    """Base class for Azure-specific errors."""

    def __init__(
        self,
        message: str,
        azure_error_code: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.azure_error_code = azure_error_code
        self.correlation_id = correlation_id
        self.details = details or {}


class AuthenticationError(ProviderError):
    """Raised when authentication with a cloud provider fails."""

    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class VpnGatewayError(VpnError):
    """Base class for VPN gateway-related errors."""
    pass


class VpnGatewayNotFoundError(VpnGatewayError):
    """Raised when a VPN gateway cannot be found."""

    def __init__(
        self,
        message: str,
        gateway_id: str,
        provider: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.gateway_id = gateway_id
        self.provider = provider
        self.details = details or {}


class VpnGatewayCreationError(VpnGatewayError):
    """Raised when creating a VPN gateway fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.details = details or {}


class VpnGatewayDeletionError(VpnGatewayError):
    """Raised when deleting a VPN gateway fails."""

    def __init__(
        self,
        message: str,
        gateway_id: str,
        provider: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.gateway_id = gateway_id
        self.provider = provider
        self.details = details or {}


class VpnConnectionError(VpnError):
    """Base class for VPN connection-related errors."""
    pass


class VpnConnectionNotFoundError(VpnConnectionError):
    """Raised when a VPN connection cannot be found."""

    def __init__(
        self,
        message: str,
        connection_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.connection_id = connection_id
        self.details = details or {}


class VpnConnectionCreationError(VpnConnectionError):
    """Raised when creating a VPN connection fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.details = details or {}


class VpnConnectionDeletionError(VpnConnectionError):
    """Raised when deleting a VPN connection fails."""

    def __init__(
        self,
        message: str,
        connection_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.connection_id = connection_id
        self.details = details or {}


class VpnConnectionUpdateError(VpnConnectionError):
    """Raised when updating a VPN connection fails."""

    def __init__(
        self,
        message: str,
        connection_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.connection_id = connection_id
        self.details = details or {}


class TunnelError(VpnError):
    """Base class for VPN tunnel-related errors."""
    pass


class TunnelConfigurationError(TunnelError):
    """Raised when VPN tunnel configuration is invalid."""

    def __init__(
        self,
        message: str,
        tunnel_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.tunnel_id = tunnel_id
        self.details = details or {}


class TunnelOperationError(TunnelError):
    """Raised when a VPN tunnel operation fails."""

    def __init__(
        self,
        message: str,
        tunnel_id: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.tunnel_id = tunnel_id
        self.operation = operation
        self.details = details or {}


class RouteError(VpnError):
    """Base class for VPN route-related errors."""
    pass


class RouteConfigurationError(RouteError):
    """Raised when VPN route configuration is invalid."""

    def __init__(
        self,
        message: str,
        route_details: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.route_details = route_details
        self.details = details or {}


class RouteOperationError(RouteError):
    """Raised when a VPN route operation fails."""

    def __init__(
        self,
        message: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}


class BgpError(VpnError):
    """Base class for BGP-related errors."""
    pass


class BgpConfigurationError(BgpError):
    """Raised when BGP configuration is invalid."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.details = details or {}


class BgpOperationError(BgpError):
    """Raised when a BGP operation fails."""

    def __init__(
        self,
        message: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}


class MonitoringError(VpnError):
    """Base class for VPN monitoring-related errors."""
    pass


class MetricsCollectionError(MonitoringError):
    """Raised when collecting VPN metrics fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        metric_names: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.metric_names = metric_names or []
        self.details = details or {}


class AlertError(MonitoringError):
    """Raised when VPN alert operations fail."""

    def __init__(
        self,
        message: str,
        alert_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.alert_id = alert_id
        self.details = details or {}
