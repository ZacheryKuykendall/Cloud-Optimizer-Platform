"""Manager for AWS-GCP VPN connections.

This module provides a high-level manager for establishing and managing
VPN connections between AWS Virtual Private Gateways and Google Cloud VPN Gateways.
"""

import logging
import uuid
from typing import Dict, List, Optional, Set, Tuple

from cloud_network_manager.vpn_modules.aws_gcp.aws_client import AwsVpnClient
from cloud_network_manager.vpn_modules.aws_gcp.gcp_client import GcpVpnClient
from cloud_network_manager.vpn_modules.aws_gcp.exceptions import (
    ValidationError,
    VpnConnectionCreationError,
    VpnConnectionDeletionError,
    VpnConnectionNotFoundError,
    VpnGatewayCreationError,
)
from cloud_network_manager.vpn_modules.aws_gcp.models import (
    AwsVpnGateway,
    GcpVpnGateway,
    BgpConfig,
    TunnelConfig,
    VpnConnection,
    VpnStatus,
)

logger = logging.getLogger(__name__)


class AwsGcpVpnManager:
    """Manager for AWS-GCP VPN connections."""

    def __init__(
        self,
        aws_client: AwsVpnClient,
        gcp_client: GcpVpnClient,
    ):
        """Initialize AWS-GCP VPN manager.

        Args:
            aws_client: AWS VPN client
            gcp_client: GCP VPN client
        """
        self.aws_client = aws_client
        self.gcp_client = gcp_client

    async def create_vpn_connection(
        self,
        name: str,
        aws_vpc_id: str,
        aws_region: str,
        gcp_network: str,
        gcp_region: str,
        tunnels: List[TunnelConfig],
        enable_bgp: bool = False,
        aws_asn: Optional[int] = None,
        gcp_asn: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> VpnConnection:
        """Create a VPN connection between AWS and GCP.

        Args:
            name: Connection name
            aws_vpc_id: AWS VPC ID
            aws_region: AWS region
            gcp_network: GCP VPC network name
            gcp_region: GCP region
            tunnels: List of tunnel configurations
            enable_bgp: Whether to enable BGP
            aws_asn: Optional AWS ASN for BGP
            gcp_asn: Optional GCP ASN for BGP
            labels: Optional resource labels

        Returns:
            Created VPN connection

        Raises:
            ValidationError: If configuration is invalid
            VpnGatewayCreationError: If gateway creation fails
            VpnConnectionCreationError: If connection creation fails
        """
        # Validate configuration
        if enable_bgp and (not aws_asn or not gcp_asn):
            raise ValidationError(
                "Both AWS and GCP ASNs must be provided when BGP is enabled"
            )

        if len(tunnels) not in (1, 2):
            raise ValidationError(
                "Must specify either 1 or 2 tunnels"
            )

        try:
            # Create AWS Virtual Private Gateway
            aws_gateway = await self.aws_client.create_vpn_gateway(
                vpc_id=aws_vpc_id,
                availability_zones={f"{aws_region}a", f"{aws_region}b"},
                asn=aws_asn if enable_bgp else None,
                tags=labels
            )

            # Create GCP VPN Gateway
            gcp_gateway = await self.gcp_client.create_vpn_gateway(
                name=f"{name}-gcp",
                network=gcp_network,
                region=gcp_region,
                labels=labels
            )

            # Create GCP VPN Tunnels
            tunnel_ids = []
            for i, tunnel in enumerate(tunnels):
                tunnel_id = await self.gcp_client.create_vpn_tunnel(
                    name=f"{name}-tunnel-{i+1}",
                    region=gcp_region,
                    gateway_name=gcp_gateway.gateway_id,
                    peer_ip=aws_gateway.public_ip_address,
                    shared_key=tunnel.preshared_key,
                    local_traffic_selector=[],  # Will be configured by routes
                    remote_traffic_selector=[],  # Will be configured by routes
                    ike_version=2,  # AWS supports IKEv2
                    labels=labels
                )
                tunnel_ids.append(tunnel_id)

            # Create AWS Customer Gateway
            customer_gateway_id = await self.aws_client.create_customer_gateway(
                ip_address=gcp_gateway.vpn_interfaces[0],  # Use first interface
                bgp_asn=gcp_asn if enable_bgp else 65000,
                tags=labels
            )

            # Create AWS VPN Connection
            aws_connection = await self.aws_client.create_vpn_connection(
                vpn_gateway_id=aws_gateway.vpn_gateway_id,
                customer_gateway_id=customer_gateway_id,
                tunnels=tunnels,
                tags=labels
            )

            # Return combined connection details
            return VpnConnection(
                id=f"{aws_connection.id}:{gcp_gateway.gateway_id}",
                name=name,
                description=f"VPN connection between AWS VPC {aws_vpc_id} and GCP VPC {gcp_network}",
                aws_gateway=aws_gateway,
                gcp_gateway=gcp_gateway,
                tunnels=tunnels,
                routes=[],  # Routes will be configured separately
                bgp_config=BgpConfig(
                    enabled=enable_bgp,
                    asn=aws_asn,
                    bgp_peer_ip=gcp_gateway.vpn_interfaces[0],
                    bgp_peer_asn=gcp_asn
                ) if enable_bgp else None,
                status=VpnStatus.PENDING,
                labels=labels or {}
            )

        except Exception as e:
            # Clean up any created resources on failure
            if "aws_gateway" in locals():
                try:
                    await self.aws_client.delete_vpn_gateway(
                        gateway_id=aws_gateway.vpn_gateway_id,
                        vpc_id=aws_vpc_id
                    )
                except Exception:
                    pass

            if "gcp_gateway" in locals():
                try:
                    await self.gcp_client.delete_vpn_gateway(
                        name=gcp_gateway.gateway_id,
                        region=gcp_region
                    )
                except Exception:
                    pass

            if isinstance(e, (ValidationError, VpnGatewayCreationError)):
                raise
            raise VpnConnectionCreationError(
                f"Failed to create VPN connection: {str(e)}",
                details={
                    "name": name,
                    "aws_vpc_id": aws_vpc_id,
                    "gcp_network": gcp_network,
                }
            ) from e

    async def delete_vpn_connection(
        self,
        connection_id: str,
        aws_vpc_id: str,
        gcp_region: str
    ) -> None:
        """Delete a VPN connection.

        Args:
            connection_id: Connection ID (format: aws_id:gcp_id)
            aws_vpc_id: AWS VPC ID
            gcp_region: GCP region

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            # Parse connection IDs
            aws_id, gcp_id = connection_id.split(":")

            # Get connection details
            aws_connection = await self.aws_client.get_vpn_connection(aws_id)

            # Delete AWS connection and gateways
            await self.aws_client.delete_vpn_connection(aws_id)
            await self.aws_client.delete_customer_gateway(
                aws_connection.customer_gateway_id
            )
            await self.aws_client.delete_vpn_gateway(
                gateway_id=aws_connection.vpn_gateway_id,
                vpc_id=aws_vpc_id
            )

            # Delete GCP gateway and tunnels
            await self.gcp_client.delete_vpn_gateway(
                name=gcp_id,
                region=gcp_region
            )

        except Exception as e:
            if isinstance(e, VpnConnectionNotFoundError):
                raise
            raise VpnConnectionDeletionError(
                f"Failed to delete VPN connection: {str(e)}",
                connection_id=connection_id
            ) from e

    async def get_vpn_connection(
        self,
        connection_id: str,
        gcp_region: str
    ) -> VpnConnection:
        """Get VPN connection details.

        Args:
            connection_id: Connection ID (format: aws_id:gcp_id)
            gcp_region: GCP region

        Returns:
            VPN connection details

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
        """
        try:
            # Parse connection IDs
            aws_id, gcp_id = connection_id.split(":")

            # Get connection details from both providers
            aws_connection = await self.aws_client.get_vpn_connection(aws_id)
            gcp_gateway = await self.gcp_client.get_vpn_gateway(
                name=gcp_id,
                region=gcp_region
            )

            # Determine overall connection status
            if aws_connection.status == VpnStatus.AVAILABLE:
                status = VpnStatus.AVAILABLE
            elif aws_connection.status == VpnStatus.FAILED:
                status = VpnStatus.FAILED
            else:
                status = VpnStatus.PENDING

            # Combine connection details
            return VpnConnection(
                id=connection_id,
                name=aws_connection.name,
                description=aws_connection.description,
                aws_gateway=aws_connection.aws_gateway,
                gcp_gateway=gcp_gateway,
                tunnels=aws_connection.tunnels,
                routes=aws_connection.routes,
                bgp_config=aws_connection.bgp_config,
                status=status,
                labels=aws_connection.labels
            )

        except Exception as e:
            if isinstance(e, VpnConnectionNotFoundError):
                raise
            raise VpnConnectionNotFoundError(
                f"Failed to get VPN connection: {str(e)}",
                connection_id=connection_id
            ) from e

    async def list_vpn_connections(
        self,
        aws_region: str,
        gcp_region: str,
        labels: Optional[Dict[str, str]] = None
    ) -> List[VpnConnection]:
        """List VPN connections.

        Args:
            aws_region: AWS region
            gcp_region: GCP region
            labels: Optional labels to filter by

        Returns:
            List of VPN connections
        """
        # TODO: Implement listing VPN connections from both providers
        # This requires additional AWS/GCP client methods to list connections
        return []
