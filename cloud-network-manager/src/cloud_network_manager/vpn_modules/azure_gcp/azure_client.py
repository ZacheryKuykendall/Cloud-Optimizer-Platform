"""Azure client for VPN operations.

This module provides a client for managing Azure VPN resources including
Virtual Network Gateways and Local Network Gateways for GCP connectivity.
"""

import logging
from typing import Dict, List, Optional

from azure.core.exceptions import AzureError as AzureCoreError
from azure.identity import ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import (
    AddressSpace,
    BgpSettings,
    IPConfigurationBgpSettings,
    LocalNetworkGateway,
    VirtualNetworkGateway,
    VirtualNetworkGatewayConnection,
    VirtualNetworkGatewayIPConfiguration,
    VirtualNetworkGatewaySku,
)

from cloud_network_manager.vpn_modules.azure_gcp.exceptions import (
    AuthenticationError,
    AzureError,
    VpnGatewayCreationError,
    VpnGatewayDeletionError,
    VpnGatewayNotFoundError,
    VpnConnectionCreationError,
    VpnConnectionDeletionError,
    VpnConnectionNotFoundError,
    VpnConnectionUpdateError,
)
from cloud_network_manager.vpn_modules.azure_gcp.models import (
    AzureVNetGateway,
    BgpConfig,
    RouteEntry,
    TunnelConfig,
    VpnConnection,
    VpnStatus,
)

logger = logging.getLogger(__name__)


class AzureVpnClient:
    """Client for managing Azure VPN resources."""

    def __init__(
        self,
        subscription_id: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
    ):
        """Initialize Azure VPN client.

        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure tenant ID
            client_id: Azure client ID
            client_secret: Azure client secret

        Raises:
            AuthenticationError: If Azure credentials are invalid
        """
        try:
            self.subscription_id = subscription_id
            self.credentials = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
            self.network_client = NetworkManagementClient(
                credential=self.credentials,
                subscription_id=subscription_id,
            )

        except AzureCoreError as e:
            raise AuthenticationError(
                f"Failed to initialize Azure client: {str(e)}",
                provider="azure"
            ) from e

    async def create_vnet_gateway(
        self,
        name: str,
        resource_group: str,
        location: str,
        vnet_name: str,
        subnet_name: str = "GatewaySubnet",
        sku: str = "VpnGw1",
        generation: str = "Generation1",
        asn: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> AzureVNetGateway:
        """Create a Virtual Network Gateway.

        Args:
            name: Gateway name
            resource_group: Resource group name
            location: Azure region
            vnet_name: Virtual network name
            subnet_name: Subnet name (default: GatewaySubnet)
            sku: Gateway SKU (e.g., VpnGw1, VpnGw2)
            generation: Gateway generation
            asn: Optional ASN for BGP
            tags: Optional resource tags

        Returns:
            Created VNet gateway

        Raises:
            VpnGatewayCreationError: If gateway creation fails
        """
        try:
            # Get VNet and subnet
            vnet = self.network_client.virtual_networks.get(
                resource_group_name=resource_group,
                virtual_network_name=vnet_name,
            )
            subnet = next(
                (s for s in vnet.subnets if s.name == subnet_name),
                None
            )
            if not subnet:
                raise VpnGatewayCreationError(
                    f"Subnet {subnet_name} not found in VNet {vnet_name}",
                    provider="azure",
                    details={
                        "resource_group": resource_group,
                        "vnet_name": vnet_name,
                    }
                )

            # Create public IP for gateway
            public_ip = self.network_client.public_ip_addresses.begin_create_or_update(
                resource_group_name=resource_group,
                public_ip_address_name=f"{name}-ip",
                parameters={
                    "location": location,
                    "sku": {"name": "Standard"},
                    "public_ip_allocation_method": "Static",
                    "public_ip_address_version": "IPv4"
                }
            ).result()

            # Prepare gateway configuration
            ip_config = VirtualNetworkGatewayIPConfiguration(
                name="default",
                private_ip_allocation_method="Dynamic",
                subnet=subnet,
                public_ip_address=public_ip,
            )

            bgp_settings = None
            if asn:
                bgp_settings = BgpSettings(
                    asn=asn,
                    bgp_peering_address="",  # Will be auto-assigned
                )

            # Create gateway
            poller = self.network_client.virtual_network_gateways.begin_create_or_update(
                resource_group_name=resource_group,
                virtual_network_gateway_name=name,
                parameters=VirtualNetworkGateway(
                    location=location,
                    ip_configurations=[ip_config],
                    gateway_type="Vpn",
                    vpn_type="RouteBased",  # GCP requires route-based VPNs
                    enable_bgp=bool(asn),
                    sku=VirtualNetworkGatewaySku(
                        name=sku,
                        tier=sku,
                    ),
                    vpn_gateway_generation=generation,
                    bgp_settings=bgp_settings,
                    tags=tags,
                )
            )
            gateway = poller.result()

            return AzureVNetGateway(
                gateway_id=gateway.id,
                vnet_name=vnet_name,
                resource_group=resource_group,
                location=location,
                sku=sku,
                generation=generation,
                active_active=gateway.active_active,
                public_ip_address=public_ip.ip_address,
                tags=gateway.tags or {}
            )

        except Exception as e:
            if isinstance(e, VpnGatewayCreationError):
                raise
            raise VpnGatewayCreationError(
                f"Failed to create VNet gateway: {str(e)}",
                provider="azure",
                details={
                    "name": name,
                    "resource_group": resource_group,
                    "vnet_name": vnet_name,
                }
            ) from e

    async def delete_vnet_gateway(
        self,
        name: str,
        resource_group: str
    ) -> None:
        """Delete a Virtual Network Gateway.

        Args:
            name: Gateway name
            resource_group: Resource group name

        Raises:
            VpnGatewayNotFoundError: If gateway does not exist
            VpnGatewayDeletionError: If deletion fails
        """
        try:
            # Delete gateway
            poller = self.network_client.virtual_network_gateways.begin_delete(
                resource_group_name=resource_group,
                virtual_network_gateway_name=name,
            )
            poller.result()

            # Delete associated public IP
            try:
                self.network_client.public_ip_addresses.begin_delete(
                    resource_group_name=resource_group,
                    public_ip_address_name=f"{name}-ip"
                ).result()
            except Exception:
                # Ignore errors deleting public IP
                pass

        except Exception as e:
            if "ResourceNotFound" in str(e):
                raise VpnGatewayNotFoundError(
                    f"VNet gateway not found: {name}",
                    gateway_id=name,
                    provider="azure"
                ) from e
            raise VpnGatewayDeletionError(
                f"Failed to delete VNet gateway: {str(e)}",
                gateway_id=name,
                provider="azure",
                details={"resource_group": resource_group}
            ) from e

    async def get_vnet_gateway(
        self,
        name: str,
        resource_group: str
    ) -> AzureVNetGateway:
        """Get Virtual Network Gateway details.

        Args:
            name: Gateway name
            resource_group: Resource group name

        Returns:
            VNet gateway details

        Raises:
            VpnGatewayNotFoundError: If gateway does not exist
        """
        try:
            gateway = self.network_client.virtual_network_gateways.get(
                resource_group_name=resource_group,
                virtual_network_gateway_name=name,
            )

            # Get VNet name from subnet ID
            vnet_name = gateway.ip_configurations[0].subnet.id.split("/")[-3]

            # Get public IP address
            public_ip = None
            if gateway.ip_configurations[0].public_ip_address:
                public_ip = self.network_client.public_ip_addresses.get(
                    resource_group_name=resource_group,
                    public_ip_address_name=gateway.ip_configurations[0].public_ip_address.id.split("/")[-1]
                ).ip_address

            return AzureVNetGateway(
                gateway_id=gateway.id,
                vnet_name=vnet_name,
                resource_group=resource_group,
                location=gateway.location,
                sku=gateway.sku.name,
                generation=gateway.vpn_gateway_generation,
                active_active=gateway.active_active,
                public_ip_address=public_ip,
                tags=gateway.tags or {}
            )

        except Exception as e:
            if "ResourceNotFound" in str(e):
                raise VpnGatewayNotFoundError(
                    f"VNet gateway not found: {name}",
                    gateway_id=name,
                    provider="azure"
                ) from e
            raise AzureError(
                f"Failed to get VNet gateway: {str(e)}",
                azure_error_code=str(e)
            ) from e

    async def create_local_network_gateway(
        self,
        name: str,
        resource_group: str,
        location: str,
        gateway_ip: str,
        address_spaces: List[str],
        asn: Optional[int] = None,
        bgp_peering_address: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a Local Network Gateway.

        Args:
            name: Gateway name
            resource_group: Resource group name
            location: Azure region
            gateway_ip: Public IP of the GCP VPN gateway
            address_spaces: List of GCP VPC address spaces
            asn: Optional ASN for BGP
            bgp_peering_address: Optional BGP peering address
            tags: Optional resource tags

        Returns:
            ID of created local network gateway

        Raises:
            VpnConnectionCreationError: If creation fails
        """
        try:
            bgp_settings = None
            if asn and bgp_peering_address:
                bgp_settings = BgpSettings(
                    asn=asn,
                    bgp_peering_address=bgp_peering_address,
                )

            poller = self.network_client.local_network_gateways.begin_create_or_update(
                resource_group_name=resource_group,
                local_network_gateway_name=name,
                parameters=LocalNetworkGateway(
                    location=location,
                    local_network_address_space=AddressSpace(
                        address_prefixes=address_spaces,
                    ),
                    gateway_ip_address=gateway_ip,
                    bgp_settings=bgp_settings,
                    tags=tags,
                )
            )
            gateway = poller.result()
            return gateway.id

        except Exception as e:
            raise VpnConnectionCreationError(
                f"Failed to create local network gateway: {str(e)}",
                details={
                    "name": name,
                    "resource_group": resource_group,
                    "gateway_ip": gateway_ip,
                }
            ) from e

    async def delete_local_network_gateway(
        self,
        name: str,
        resource_group: str
    ) -> None:
        """Delete a Local Network Gateway.

        Args:
            name: Gateway name
            resource_group: Resource group name

        Raises:
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            poller = self.network_client.local_network_gateways.begin_delete(
                resource_group_name=resource_group,
                local_network_gateway_name=name,
            )
            poller.result()

        except Exception as e:
            if "ResourceNotFound" not in str(e):
                raise VpnConnectionDeletionError(
                    f"Failed to delete local network gateway: {str(e)}",
                    connection_id=name
                ) from e

    async def create_vpn_connection(
        self,
        name: str,
        resource_group: str,
        vnet_gateway_name: str,
        local_gateway_name: str,
        shared_key: str,
        enable_bgp: bool = False,
        tags: Optional[Dict[str, str]] = None
    ) -> VpnConnection:
        """Create a VPN Connection.

        Args:
            name: Connection name
            resource_group: Resource group name
            vnet_gateway_name: Virtual Network Gateway name
            local_gateway_name: Local Network Gateway name
            shared_key: Pre-shared key
            enable_bgp: Whether to enable BGP
            tags: Optional resource tags

        Returns:
            Created VPN connection

        Raises:
            VpnConnectionCreationError: If creation fails
        """
        try:
            poller = self.network_client.virtual_network_gateway_connections.begin_create_or_update(
                resource_group_name=resource_group,
                virtual_network_gateway_connection_name=name,
                parameters=VirtualNetworkGatewayConnection(
                    name=name,
                    location=None,  # Will inherit from gateway
                    virtual_network_gateway1=self.network_client.virtual_network_gateways.get(
                        resource_group_name=resource_group,
                        virtual_network_gateway_name=vnet_gateway_name,
                    ),
                    local_network_gateway2=self.network_client.local_network_gateways.get(
                        resource_group_name=resource_group,
                        local_network_gateway_name=local_gateway_name,
                    ),
                    connection_type="IPsec",
                    routing_weight=0,
                    shared_key=shared_key,
                    enable_bgp=enable_bgp,
                    use_policy_based_traffic_selectors=False,  # GCP requires route-based
                    tags=tags,
                )
            )
            connection = poller.result()

            # Get full connection details
            return await self.get_vpn_connection(name, resource_group)

        except Exception as e:
            raise VpnConnectionCreationError(
                f"Failed to create VPN connection: {str(e)}",
                details={
                    "name": name,
                    "resource_group": resource_group,
                    "vnet_gateway_name": vnet_gateway_name,
                }
            ) from e

    async def delete_vpn_connection(
        self,
        name: str,
        resource_group: str
    ) -> None:
        """Delete a VPN Connection.

        Args:
            name: Connection name
            resource_group: Resource group name

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            poller = self.network_client.virtual_network_gateway_connections.begin_delete(
                resource_group_name=resource_group,
                virtual_network_gateway_connection_name=name,
            )
            poller.result()

        except Exception as e:
            if "ResourceNotFound" in str(e):
                raise VpnConnectionNotFoundError(
                    f"VPN connection not found: {name}",
                    connection_id=name
                ) from e
            raise VpnConnectionDeletionError(
                f"Failed to delete VPN connection: {str(e)}",
                connection_id=name
            ) from e

    async def get_vpn_connection(
        self,
        name: str,
        resource_group: str
    ) -> VpnConnection:
        """Get VPN Connection details.

        Args:
            name: Connection name
            resource_group: Resource group name

        Returns:
            VPN connection details

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
        """
        try:
            connection = self.network_client.virtual_network_gateway_connections.get(
                resource_group_name=resource_group,
                virtual_network_gateway_connection_name=name,
            )

            # Get associated gateways
            vnet_gateway = await self.get_vnet_gateway(
                name=connection.virtual_network_gateway1.name,
                resource_group=resource_group,
            )

            # Parse tunnel configurations
            tunnels = []
            if connection.shared_key:
                tunnels.append(TunnelConfig(
                    inside_cidr=None,  # Azure doesn't expose this
                    preshared_key=connection.shared_key,
                ))

            # Parse BGP configuration
            bgp_config = None
            if connection.enable_bgp:
                bgp_config = BgpConfig(
                    enabled=True,
                    asn=connection.virtual_network_gateway1.bgp_settings.asn,
                    bgp_peer_ip=connection.local_network_gateway2.bgp_settings.bgp_peering_address,
                    bgp_peer_asn=connection.local_network_gateway2.bgp_settings.asn
                )

            return VpnConnection(
                id=connection.id,
                name=connection.name,
                description=None,  # Azure doesn't support descriptions
                azure_gateway=vnet_gateway,
                gcp_gateway=None,  # Will be set by manager
                tunnels=tunnels,
                routes=[],  # Azure handles routes differently
                bgp_config=bgp_config,
                status=VpnStatus(connection.connection_status.lower()),
                labels=connection.tags or {}  # Use labels for GCP compatibility
            )

        except Exception as e:
            if "ResourceNotFound" in str(e):
                raise VpnConnectionNotFoundError(
                    f"VPN connection not found: {name}",
                    connection_id=name
                ) from e
            raise AzureError(
                f"Failed to get VPN connection: {str(e)}",
                azure_error_code=str(e)
            ) from e
