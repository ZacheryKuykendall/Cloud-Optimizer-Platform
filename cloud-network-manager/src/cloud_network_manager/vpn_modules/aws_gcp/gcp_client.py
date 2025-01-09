"""GCP client for VPN operations.

This module provides a client for managing Google Cloud VPN resources including
VPN Gateways, Cloud Routers, and VPN Tunnels.
"""

import logging
from typing import Dict, List, Optional, Set

from google.api_core import operation, retry
from google.cloud import compute_v1
from google.cloud.compute_v1.types import compute as compute_types

from cloud_network_manager.vpn_modules.aws_gcp.exceptions import (
    AuthenticationError,
    GcpError,
    OperationTimeoutError,
    ValidationError,
    VpnConnectionCreationError,
    VpnConnectionDeletionError,
    VpnConnectionNotFoundError,
    VpnGatewayCreationError,
    VpnGatewayDeletionError,
    VpnGatewayNotFoundError,
)
from cloud_network_manager.vpn_modules.aws_gcp.models import (
    BgpConfig,
    GcpVpnGateway,
    RouteEntry,
    TunnelConfig,
    VpnConnection,
    VpnStatus,
)

logger = logging.getLogger(__name__)


class GcpVpnClient:
    """Client for managing GCP VPN resources."""

    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        credentials_dict: Optional[Dict] = None,
    ):
        """Initialize GCP VPN client.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file
            credentials_dict: Service account credentials as dictionary

        Raises:
            AuthenticationError: If GCP credentials are invalid
        """
        try:
            self.project_id = project_id
            
            # Initialize clients
            self.compute_client = compute_v1.VpnGatewaysClient()
            self.vpn_tunnels_client = compute_v1.VpnTunnelsClient()
            self.routers_client = compute_v1.RoutersClient()
            self.operations_client = compute_v1.GlobalOperationsClient()

        except Exception as e:
            raise AuthenticationError(
                f"Failed to initialize GCP client: {str(e)}",
                provider="gcp"
            ) from e

    def _wait_for_operation(
        self,
        operation_future: operation.Operation,
        operation_type: str,
        timeout: int = 300
    ) -> None:
        """Wait for a long-running operation to complete.

        Args:
            operation_future: Operation future to wait for
            operation_type: Type of operation (for error messages)
            timeout: Timeout in seconds

        Raises:
            OperationTimeoutError: If operation times out
            GcpError: If operation fails
        """
        try:
            operation_future.result(timeout=timeout)
        except Exception as e:
            if isinstance(e, TimeoutError):
                raise OperationTimeoutError(
                    f"Operation timed out after {timeout} seconds",
                    operation_id=operation_future.operation.name,
                    operation_type=operation_type
                ) from e
            raise GcpError(
                f"Operation failed: {str(e)}",
                operation_id=operation_future.operation.name
            ) from e

    async def create_vpn_gateway(
        self,
        name: str,
        network: str,
        region: str,
        stack_type: str = "IPV4_ONLY",
        labels: Optional[Dict[str, str]] = None
    ) -> GcpVpnGateway:
        """Create a VPN Gateway.

        Args:
            name: Gateway name
            network: VPC network name or self-link
            region: GCP region
            stack_type: IP stack type (IPV4_ONLY or IPV4_IPV6)
            labels: Optional resource labels

        Returns:
            Created VPN gateway

        Raises:
            VpnGatewayCreationError: If gateway creation fails
        """
        try:
            # Prepare gateway configuration
            gateway = compute_types.VpnGateway()
            gateway.name = name
            gateway.network = (
                network if network.startswith("projects/")
                else f"projects/{self.project_id}/global/networks/{network}"
            )
            gateway.stack_type = stack_type
            if labels:
                gateway.labels = labels

            # Create gateway
            operation_future = self.compute_client.insert(
                project=self.project_id,
                region=region,
                vpn_gateway_resource=gateway
            )

            # Wait for creation to complete
            self._wait_for_operation(
                operation_future,
                "vpn_gateway_creation"
            )

            # Get created gateway
            return await self.get_vpn_gateway(name, region)

        except Exception as e:
            if isinstance(e, OperationTimeoutError):
                raise
            raise VpnGatewayCreationError(
                f"Failed to create VPN gateway: {str(e)}",
                provider="gcp",
                details={
                    "name": name,
                    "network": network,
                    "region": region,
                }
            ) from e

    async def delete_vpn_gateway(
        self,
        name: str,
        region: str
    ) -> None:
        """Delete a VPN Gateway.

        Args:
            name: Gateway name
            region: GCP region

        Raises:
            VpnGatewayNotFoundError: If gateway does not exist
            VpnGatewayDeletionError: If deletion fails
        """
        try:
            # Delete gateway
            operation_future = self.compute_client.delete(
                project=self.project_id,
                region=region,
                vpn_gateway=name
            )

            # Wait for deletion to complete
            self._wait_for_operation(
                operation_future,
                "vpn_gateway_deletion"
            )

        except Exception as e:
            if isinstance(e, OperationTimeoutError):
                raise
            if "not found" in str(e).lower():
                raise VpnGatewayNotFoundError(
                    f"VPN gateway not found: {name}",
                    gateway_id=name,
                    provider="gcp"
                ) from e
            raise VpnGatewayDeletionError(
                f"Failed to delete VPN gateway: {str(e)}",
                gateway_id=name,
                provider="gcp",
                details={"region": region}
            ) from e

    async def get_vpn_gateway(
        self,
        name: str,
        region: str
    ) -> GcpVpnGateway:
        """Get VPN Gateway details.

        Args:
            name: Gateway name
            region: GCP region

        Returns:
            VPN gateway details

        Raises:
            VpnGatewayNotFoundError: If gateway does not exist
        """
        try:
            gateway = self.compute_client.get(
                project=self.project_id,
                region=region,
                vpn_gateway=name
            )

            # Extract network name from self-link
            network = gateway.network.split("/")[-1]

            # Get gateway interface IPs
            vpn_interfaces = [
                interface.ip_address
                for interface in gateway.vpn_interfaces
            ]

            return GcpVpnGateway(
                gateway_id=gateway.id,
                project_id=self.project_id,
                network=network,
                region=region,
                vpn_interfaces=vpn_interfaces,
                stack_type=gateway.stack_type,
                labels=dict(gateway.labels) if gateway.labels else {}
            )

        except Exception as e:
            if "not found" in str(e).lower():
                raise VpnGatewayNotFoundError(
                    f"VPN gateway not found: {name}",
                    gateway_id=name,
                    provider="gcp"
                ) from e
            raise GcpError(
                f"Failed to get VPN gateway: {str(e)}",
                gcp_error_code=str(e)
            ) from e

    async def create_vpn_tunnel(
        self,
        name: str,
        region: str,
        gateway_name: str,
        peer_ip: str,
        shared_key: str,
        local_traffic_selector: List[str],
        remote_traffic_selector: List[str],
        ike_version: int = 2,
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a VPN Tunnel.

        Args:
            name: Tunnel name
            region: GCP region
            gateway_name: VPN gateway name
            peer_ip: Peer gateway IP address
            shared_key: Pre-shared key
            local_traffic_selector: Local traffic selectors
            remote_traffic_selector: Remote traffic selectors
            ike_version: IKE protocol version
            labels: Optional resource labels

        Returns:
            ID of created tunnel

        Raises:
            VpnConnectionCreationError: If tunnel creation fails
        """
        try:
            # Prepare tunnel configuration
            tunnel = compute_types.VpnTunnel()
            tunnel.name = name
            tunnel.peer_ip = peer_ip
            tunnel.shared_secret = shared_key
            tunnel.ike_version = ike_version
            tunnel.vpn_gateway = f"projects/{self.project_id}/regions/{region}/vpnGateways/{gateway_name}"
            tunnel.local_traffic_selector = local_traffic_selector
            tunnel.remote_traffic_selector = remote_traffic_selector
            if labels:
                tunnel.labels = labels

            # Create tunnel
            operation_future = self.vpn_tunnels_client.insert(
                project=self.project_id,
                region=region,
                vpn_tunnel_resource=tunnel
            )

            # Wait for creation to complete
            self._wait_for_operation(
                operation_future,
                "vpn_tunnel_creation"
            )

            return operation_future.operation.target_id

        except Exception as e:
            if isinstance(e, OperationTimeoutError):
                raise
            raise VpnConnectionCreationError(
                f"Failed to create VPN tunnel: {str(e)}",
                details={
                    "name": name,
                    "region": region,
                    "gateway_name": gateway_name,
                }
            ) from e

    async def delete_vpn_tunnel(
        self,
        name: str,
        region: str
    ) -> None:
        """Delete a VPN Tunnel.

        Args:
            name: Tunnel name
            region: GCP region

        Raises:
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            # Delete tunnel
            operation_future = self.vpn_tunnels_client.delete(
                project=self.project_id,
                region=region,
                vpn_tunnel=name
            )

            # Wait for deletion to complete
            self._wait_for_operation(
                operation_future,
                "vpn_tunnel_deletion"
            )

        except Exception as e:
            if isinstance(e, OperationTimeoutError):
                raise
            if "not found" not in str(e).lower():
                raise VpnConnectionDeletionError(
                    f"Failed to delete VPN tunnel: {str(e)}",
                    connection_id=name
                ) from e

    async def get_vpn_tunnel(
        self,
        name: str,
        region: str
    ) -> compute_types.VpnTunnel:
        """Get VPN Tunnel details.

        Args:
            name: Tunnel name
            region: GCP region

        Returns:
            VPN tunnel details

        Raises:
            VpnConnectionNotFoundError: If tunnel does not exist
        """
        try:
            return self.vpn_tunnels_client.get(
                project=self.project_id,
                region=region,
                vpn_tunnel=name
            )

        except Exception as e:
            if "not found" in str(e).lower():
                raise VpnConnectionNotFoundError(
                    f"VPN tunnel not found: {name}",
                    connection_id=name
                ) from e
            raise GcpError(
                f"Failed to get VPN tunnel: {str(e)}",
                gcp_error_code=str(e)
            ) from e
