"""Manager for Azure-GCP VPN connections.

This module provides a high-level manager for establishing and managing
VPN connections between Azure Virtual Network Gateways and Google Cloud VPN Gateways.
"""

import logging
import uuid
from typing import Dict, List, Optional, Set, Tuple

from cloud_network_manager.vpn_modules.azure_gcp.azure_client import AzureVpnClient
from cloud_network_manager.vpn_modules.azure_gcp.gcp_client import GcpVpnClient
from cloud_network_manager.vpn_modules.azure_gcp.exceptions import (
    ValidationError,
    VpnConnectionCreationError,
    VpnConnectionDeletionError,
    VpnConnectionNotFoundError,
    VpnGatewayCreationError,
)
from cloud_network_manager.vpn_modules.azure_gcp.models import (
    AzureVNetGateway,
    GcpVpnGateway,
    BgpConfig,
    TunnelConfig,
    VpnConnection,
    VpnStatus,
)

logger = logging.getLogger(__name__)


class AzureGcpVpnManager:
    """Manager for Azure-GCP VPN connections."""

    def __init__(
        self,
        azure_client: AzureVpnClient,
        gcp_client: GcpVpnClient,
    ):
        """Initialize Azure-GCP VPN manager.

        Args:
            azure_client: Azure VPN client
            gcp_client: GCP VPN client
        """
        self.azure_client = azure_client
        self.gcp_client = gcp_client

    async def create_vpn_connection(
        self,
        name: str,
        azure_resource_group: str,
        azure_vnet_name: str,
        azure_location: str,
        gcp_network: str,
        gcp_region: str,
        tunnels: List[TunnelConfig],
        enable_bgp: bool = False,
        azure_asn: Optional[int] = None,
        gcp_asn: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> VpnConnection:
        """Create a VPN connection between Azure and GCP.

        Args:
            name: Connection name
            azure_resource_group: Azure resource group
            azure_vnet_name: Azure VNet name
            azure_location: Azure location
            gcp_network: GCP VPC network name
            gcp_region: GCP region
            tunnels: List of tunnel configurations
            enable_bgp: Whether to enable BGP
            azure_asn: Optional Azure ASN for BGP
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
        if enable_bgp and (not azure_asn or not gcp_asn):
            raise ValidationError(
                "Both Azure and GCP ASNs must be provided when BGP is enabled"
            )

        if len(tunnels) not in (1, 2):
            raise ValidationError(
                "Must specify either 1 or 2 tunnels"
            )

        try:
            # Create Azure Virtual Network Gateway
            azure_gateway = await self.azure_client.create_vnet_gateway(
                name=f"{name}-azure",
                resource_group=azure_resource_group,
                location=azure_location,
                vnet_name=azure_vnet_name,
                asn=azure_asn if enable_bgp else None,
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
                    peer_ip=azure_gateway.public_ip_address,
                    shared_key=tunnel.preshared_key,
                    local_traffic_selector=[],  # Will be configured by routes
                    remote_traffic_selector=[],  # Will be configured by routes
                    ike_version=2,  # Azure supports IKEv2
                    labels=labels
                )
                tunnel_ids.append(tunnel_id)

            # Create Azure Local Network Gateway
            local_gateway_id = await self.azure_client.create_local_network_gateway(
                name=f"{name}-local",
                resource_group=azure_resource_group,
                location=azure_location,
                gateway_ip=gcp_gateway.vpn_interfaces[0],  # Use first interface
                address_spaces=[gcp_network],
                asn=gcp_asn if enable_bgp else None,
                bgp_peering_address=tunnel_ids[0] if enable_bgp else None,  # Use first tunnel
                tags=labels
            )

            # Create Azure VPN Connection
            azure_connection = await self.azure_client.create_vpn_connection(
                name=name,
                resource_group=azure_resource_group,
                vnet_gateway_name=azure_gateway.gateway_id.split("/")[-1],
                local_gateway_name=local_gateway_id.split("/")[-1],
                shared_key=tunnels[0].preshared_key,  # Use first tunnel's key
                enable_bgp=enable_bgp,
                tags=labels
            )

            # Return combined connection details
            return VpnConnection(
                id=f"{azure_connection.id}:{gcp_gateway.gateway_id}",
                name=name,
                description=f"VPN connection between Azure VNet {azure_vnet_name} and GCP VPC {gcp_network}",
                azure_gateway=azure_gateway,
                gcp_gateway=gcp_gateway,
                tunnels=tunnels,
                routes=[],  # Routes will be configured separately
                bgp_config=BgpConfig(
                    enabled=enable_bgp,
                    asn=azure_asn,
                    bgp_peer_ip=gcp_gateway.vpn_interfaces[0],
                    bgp_peer_asn=gcp_asn
                ) if enable_bgp else None,
                status=VpnStatus.PENDING,
                labels=labels or {}
            )

        except Exception as e:
            # Clean up any created resources on failure
            if "azure_gateway" in locals():
                try:
                    await self.azure_client.delete_vnet_gateway(
                        name=azure_gateway.gateway_id.split("/")[-1],
                        resource_group=azure_resource_group
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
                    "azure_vnet_name": azure_vnet_name,
                    "gcp_network": gcp_network,
                }
            ) from e

    async def delete_vpn_connection(
        self,
        connection_id: str,
        azure_resource_group: str,
        gcp_region: str
    ) -> None:
        """Delete a VPN connection.

        Args:
            connection_id: Connection ID (format: azure_id:gcp_id)
            azure_resource_group: Azure resource group
            gcp_region: GCP region

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            # Parse connection IDs
            azure_id, gcp_id = connection_id.split(":")

            # Get connection details
            azure_connection = await self.azure_client.get_vpn_connection(
                name=azure_id.split("/")[-1],
                resource_group=azure_resource_group
            )

            # Delete Azure connection and gateways
            await self.azure_client.delete_vpn_connection(
                name=azure_connection.name,
                resource_group=azure_resource_group
            )
            await self.azure_client.delete_local_network_gateway(
                name=azure_connection.local_network_gateway2.name,
                resource_group=azure_resource_group
            )
            await self.azure_client.delete_vnet_gateway(
                name=azure_connection.virtual_network_gateway1.name,
                resource_group=azure_resource_group
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
        azure_resource_group: str,
        gcp_region: str
    ) -> VpnConnection:
        """Get VPN connection details.

        Args:
            connection_id: Connection ID (format: azure_id:gcp_id)
            azure_resource_group: Azure resource group
            gcp_region: GCP region

        Returns:
            VPN connection details

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
        """
        try:
            # Parse connection IDs
            azure_id, gcp_id = connection_id.split(":")

            # Get connection details from both providers
            azure_connection = await self.azure_client.get_vpn_connection(
                name=azure_id.split("/")[-1],
                resource_group=azure_resource_group
            )
            gcp_gateway = await self.gcp_client.get_vpn_gateway(
                name=gcp_id,
                region=gcp_region
            )

            # Determine overall connection status
            if azure_connection.status == VpnStatus.AVAILABLE:
                status = VpnStatus.AVAILABLE
            elif azure_connection.status == VpnStatus.FAILED:
                status = VpnStatus.FAILED
            else:
                status = VpnStatus.PENDING

            # Combine connection details
            return VpnConnection(
                id=connection_id,
                name=azure_connection.name,
                description=azure_connection.description,
                azure_gateway=azure_connection.azure_gateway,
                gcp_gateway=gcp_gateway,
                tunnels=azure_connection.tunnels,
                routes=azure_connection.routes,
                bgp_config=azure_connection.bgp_config,
                status=status,
                labels=azure_connection.labels
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
        azure_resource_group: str,
        gcp_region: str,
        labels: Optional[Dict[str, str]] = None
    ) -> List[VpnConnection]:
        """List VPN connections.

        Args:
            azure_resource_group: Azure resource group
            gcp_region: GCP region
            labels: Optional labels to filter by

        Returns:
            List of VPN connections
        """
        # TODO: Implement listing VPN connections from both providers
        # This requires additional Azure/GCP client methods to list connections
        return []
