"""Custom exceptions for cloud network management.

This module defines exceptions specific to network operations and VPN
management across different cloud providers.
"""

from typing import Any, Dict, List, Optional


class CloudNetworkError(Exception):
    """Base exception for all cloud network errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(CloudNetworkError):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_value: Any = None):
        super().__init__(message)
        self.invalid_value = invalid_value


class NetworkError(CloudNetworkError):
    """Base class for network-related errors."""
    pass


class NetworkCreationError(NetworkError):
    """Raised when creating a network resource fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        network_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.network_name = network_name
        self.details = details or {}


class NetworkDeletionError(NetworkError):
    """Raised when deleting a network resource fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        network_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.network_id = network_id
        self.details = details or {}


class NetworkUpdateError(NetworkError):
    """Raised when updating a network resource fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        network_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.network_id = network_id
        self.details = details or {}


class VPNError(CloudNetworkError):
    """Base class for VPN-related errors."""
    pass


class VPNCreationError(VPNError):
    """Raised when creating a VPN connection fails."""

    def __init__(
        self,
        message: str,
        source_network: str,
        target_network: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.source_network = source_network
        self.target_network = target_network
        self.details = details or {}


class VPNDeletionError(VPNError):
    """Raised when deleting a VPN connection fails."""

    def __init__(
        self,
        message: str,
        vpn_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.vpn_id = vpn_id
        self.details = details or {}


class VPNUpdateError(VPNError):
    """Raised when updating a VPN connection fails."""

    def __init__(
        self,
        message: str,
        vpn_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.vpn_id = vpn_id
        self.details = details or {}


class VPNTunnelError(VPNError):
    """Raised when there are issues with VPN tunnels."""

    def __init__(
        self,
        message: str,
        vpn_id: str,
        tunnel_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.vpn_id = vpn_id
        self.tunnel_id = tunnel_id
        self.details = details or {}


class ProviderError(CloudNetworkError):
    """Base class for cloud provider-related errors."""
    pass


class UnsupportedProviderError(ProviderError):
    """Raised when an unsupported cloud provider is specified."""

    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class ProviderAuthenticationError(ProviderError):
    """Raised when authentication with a cloud provider fails."""

    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class ProviderAPIError(ProviderError):
    """Raised when a cloud provider API request fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        response: Optional[str] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.response = response


class RouteError(CloudNetworkError):
    """Base class for routing-related errors."""
    pass


class RouteTableError(RouteError):
    """Raised when there are issues with route tables."""

    def __init__(
        self,
        message: str,
        route_table_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.route_table_id = route_table_id
        self.details = details or {}


class RouteConflictError(RouteError):
    """Raised when there are conflicting routes."""

    def __init__(
        self,
        message: str,
        route_table_id: str,
        conflicting_routes: List[str]
    ):
        super().__init__(message)
        self.route_table_id = route_table_id
        self.conflicting_routes = conflicting_routes


class SecurityError(CloudNetworkError):
    """Base class for security-related errors."""
    pass


class SecurityGroupError(SecurityError):
    """Raised when there are issues with security groups."""

    def __init__(
        self,
        message: str,
        security_group_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.security_group_id = security_group_id
        self.details = details or {}


class NetworkACLError(SecurityError):
    """Raised when there are issues with network ACLs."""

    def __init__(
        self,
        message: str,
        acl_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.acl_id = acl_id
        self.details = details or {}


class ConfigurationError(CloudNetworkError):
    """Raised when there are issues with configuration."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ):
        super().__init__(message)
        self.config_key = config_key
        self.config_value = config_value


class StateError(CloudNetworkError):
    """Raised when there are issues with network state."""

    def __init__(
        self,
        message: str,
        state_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.state_id = state_id
        self.details = details or {}


class MonitoringError(CloudNetworkError):
    """Raised when there are issues with network monitoring."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        metric_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.metric_name = metric_name
        self.details = details or {}


class ValidationError(CloudNetworkError):
    """Raised when network validation fails."""

    def __init__(
        self,
        message: str,
        validation_errors: List[Dict[str, Any]],
        validation_warnings: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(message)
        self.validation_errors = validation_errors
        self.validation_warnings = validation_warnings or []


class ConcurrencyError(CloudNetworkError):
    """Raised when there are concurrent operation conflicts."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.operation = operation
        self.details = details or {}
