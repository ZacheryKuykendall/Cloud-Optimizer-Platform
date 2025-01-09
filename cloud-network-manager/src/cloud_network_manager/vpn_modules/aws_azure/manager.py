"""Manager for AWS-Azure VPN connections.

This module provides a high-level manager for establishing and managing
VPN connections between AWS Virtual Private Gateways and Azure Virtual
Network Gateways.
"""

import logging
import uuid
from typing import Dict, List, Optional, Set, Tuple

from cloud_network_manager.vpn_modules.aws_azure.aws_client import AwsVpnClient
from cloud_network_manager.vpn_modules.aws_azure.azure_client import AzureVpnClient
from cloud_network_manager.vpn_modules.aws_azure.exceptions import (
    ValidationError,
    VpnConnectionCreationError,
    VpnConnectionDeletionError,
    VpnConnectionNotFoundError,
    VpnGatewayCreationError,
)
from cloud_network_manager.vpn_modules.aws_azure.models import (
    AwsVpnGateway,
    AzureVNetGateway,
    BgpConfig,
    TunnelConfig,
    VpnConnection,
    VpnStatus,
)

logger = logging.getLogger(__name__)


class AwsAzureVpnManager:
    """Manager for AWS-Azure VPN connections."""

    def __init__(
        self,
        aws_client: AwsVpnClient,
        azure_client: AzureVpnClient,
    ):
        """Initialize AWS-Azure VPN manager.

        Args:
            aws_client: AWS VPN client
            azure_client: Azure VPN client
        """
        self.aws_client = aws_client
        self.azure_client = azure_client

    async def create_vpn_connection(
        self,
        name: str,
        aws_vpc_id: str,
        aws_region: str,
        azure_resource_group: str,
        azure_vnet_name: str,
        azure_location: str,
        tunnels: List[TunnelConfig],
        enable_bgp: bool = False,
        aws_asn: Optional[int] = None,
        azure_asn: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> VpnConnection:
        """Create a VPN connection between AWS and Azure.

        Args:
            name: Connection name
            aws_vpc_id: AWS VPC ID
            aws_region: AWS region
            azure_resource_group: Azure resource group
            azure_vnet_name: Azure VNet name
            azure_location: Azure location
            tunnels: List of tunnel configurations
            enable_bgp: Whether to enable BGP
            aws_asn: Optional AWS ASN for BGP
            azure_asn: Optional Azure ASN for BGP
            tags: Optional resource tags

        Returns:
            Created VPN connection

        Raises:
            ValidationError: If configuration is invalid
            VpnGatewayCreationError: If gateway creation fails
            VpnConnectionCreationError: If connection creation fails
        """
        # Validate configuration
        if enable_bgp and (not aws_asn or not azure_asn):
            raise ValidationError(
                "Both AWS and Azure ASNs must be provided when BGP is enabled"
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
                tags=tags
            )

            # Create Azure Virtual Network Gateway
            azure_gateway = await self.azure_client.create_vnet_gateway(
                name=f"{name}-gateway",
                resource_group=azure_resource_group,
                location=azure_location,
                vnet_name=azure_vnet_name,
                asn=azure_asn if enable_bgp else None,
                tags=tags
            )

            # Get Azure gateway public IP
            azure_gateway_ip = (await self.azure_client.get_vnet_gateway(
                name=azure_gateway.gateway_id.split("/")[-1],
                resource_group=azure_resource_group
            )).public_ip_address

            # Create AWS Customer Gateway
            customer_gateway_id = await self.aws_client.create_customer_gateway(
                ip_address=azure_gateway_ip,
                bgp_asn=azure_asn if enable_bgp else 65000,
                tags=tags
            )

            # Create AWS VPN Connection
            aws_connection = await self.aws_client.create_vpn_connection(
                vpn_gateway_id=aws_gateway.vpn_gateway_id,
                customer_gateway_id=customer_gateway_id,
                tunnels=tunnels,
                tags=tags
            )

            # Get AWS gateway public IPs
            aws_tunnel_ips = [t.outside_ip_address for t in aws_connection.tunnels]

            # Create Azure Local Network Gateway
            local_gateway_id = await self.azure_client.create_local_network_gateway(
                name=f"{name}-local",
                resource_group=azure_resource_group,
                location=azure_location,
                gateway_ip=aws_tunnel_ips[0],  # Use first tunnel IP
                address_spaces=[aws_vpc_id],
                asn=aws_asn if enable_bgp else None,
                bgp_peering_address=aws_connection.tunnels[0].inside_ip_address if enable_bgp else None,
                tags=tags
            )

            # Create Azure VPN Connection
            azure_connection = await self.azure_client.create_vpn_connection(
                name=name,
                resource_group=azure_resource_group,
                vnet_gateway_name=azure_gateway.gateway_id.split("/")[-1],
                local_gateway_name=local_gateway_id.split("/")[-1],
                shared_key=tunnels[0].preshared_key,
                enable_bgp=enable_bgp,
                tags=tags
            )

            # Return combined connection details
            return VpnConnection(
                id=f"{aws_connection.id}:{azure_connection.id}",
                name=name,
                description=f"VPN connection between AWS VPC {aws_vpc_id} and Azure VNet {azure_vnet_name}",
                aws_gateway=aws_gateway,
                azure_gateway=azure_gateway,
                tunnels=tunnels,
                routes=aws_connection.routes,
                bgp_config=BgpConfig(
                    enabled=enable_bgp,
                    asn=aws_asn,
                    bgp_peer_ip=azure_gateway_ip,
                    bgp_peer_asn=azure_asn
                ) if enable_bgp else None,
                status=VpnStatus.PENDING,
                tags=tags or {}
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

            if "azure_gateway" in locals():
                try:
                    await self.azure_client.delete_vnet_gateway(
                        name=azure_gateway.gateway_id.split("/")[-1],
                        resource_group=azure_resource_group
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
                    "azure_vnet_name": azure_vnet_name,
                }
            ) from e

    async def delete_vpn_connection(
        self,
        connection_id: str,
        aws_vpc_id: str,
        azure_resource_group: str
    ) -> None:
        """Delete a VPN connection.

        Args:
            connection_id: Connection ID (format: aws_id:azure_id)
            aws_vpc_id: AWS VPC ID
            azure_resource_group: Azure resource group

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            # Parse connection IDs
            aws_id, azure_id = connection_id.split(":")

            # Get connection details
            aws_connection = await self.aws_client.get_vpn_connection(aws_id)
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

            # Delete AWS connection and gateways
            await self.aws_client.delete_vpn_connection(aws_id)
            await self.aws_client.delete_customer_gateway(
                aws_connection.customer_gateway_id
            )
            await self.aws_client.delete_vpn_gateway(
                gateway_id=aws_connection.vpn_gateway_id,
                vpc_id=aws_vpc_id
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
        azure_resource_group: str
    ) -> VpnConnection:
        """Get VPN connection details.

        Args:
            connection_id: Connection ID (format: aws_id:azure_id)
            azure_resource_group: Azure resource group

        Returns:
            VPN connection details

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
        """
        try:
            # Parse connection IDs
            aws_id, azure_id = connection_id.split(":")

            # Get connection details from both providers
            aws_connection = await self.aws_client.get_vpn_connection(aws_id)
            azure_connection = await self.azure_client.get_vpn_connection(
                name=azure_id.split("/")[-1],
                resource_group=azure_resource_group
            )

            # Determine overall connection status
            if aws_connection.status == VpnStatus.AVAILABLE and azure_connection.status == VpnStatus.AVAILABLE:
                status = VpnStatus.AVAILABLE
            elif aws_connection.status == VpnStatus.FAILED or azure_connection.status == VpnStatus.FAILED:
                status = VpnStatus.FAILED
            else:
                status = VpnStatus.PENDING

            # Combine connection details
            return VpnConnection(
                id=connection_id,
                name=azure_connection.name,
                description=aws_connection.description,
                aws_gateway=aws_connection.aws_gateway,
                azure_gateway=azure_connection.azure_gateway,
                tunnels=aws_connection.tunnels,
                routes=aws_connection.routes,
                bgp_config=aws_connection.bgp_config,
                status=status,
                tags=aws_connection.tags
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
        azure_resource_group: str,
        tags: Optional[Dict[str, str]] = None
    ) -> List[VpnConnection]:
        """List VPN connections.

        Args:
            aws_region: AWS region
            azure_resource_group: Azure resource group
            tags: Optional tags to filter by

        Returns:
            List of VPN connections
        """
        # TODO: Implement listing VPN connections from both providers
        # This requires additional AWS/Azure client methods to list connections
        return []
