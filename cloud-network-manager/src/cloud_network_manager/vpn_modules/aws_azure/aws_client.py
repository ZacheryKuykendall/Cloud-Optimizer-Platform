"""AWS client for VPN operations.

This module provides a client for managing AWS VPN resources including
Virtual Private Gateways, Customer Gateways, and VPN Connections.
"""

import logging
from typing import Dict, List, Optional, Set

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from cloud_network_manager.vpn_modules.aws_azure.exceptions import (
    AuthenticationError,
    AwsError,
    VpnGatewayCreationError,
    VpnGatewayDeletionError,
    VpnGatewayNotFoundError,
    VpnConnectionCreationError,
    VpnConnectionDeletionError,
    VpnConnectionNotFoundError,
    VpnConnectionUpdateError,
)
from cloud_network_manager.vpn_modules.aws_azure.models import (
    AwsVpnGateway,
    BgpConfig,
    RouteEntry,
    TunnelConfig,
    VpnConnection,
    VpnStatus,
)

logger = logging.getLogger(__name__)


class AwsVpnClient:
    """Client for managing AWS VPN resources."""

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str,
        session_token: Optional[str] = None,
    ):
        """Initialize AWS VPN client.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region
            session_token: Optional session token for temporary credentials

        Raises:
            AuthenticationError: If AWS credentials are invalid
        """
        try:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=session_token,
                region_name=region,
            )
            self.ec2_client = self.session.client("ec2")
            self.region = region

        except (BotoCoreError, ClientError) as e:
            raise AuthenticationError(
                f"Failed to initialize AWS client: {str(e)}",
                provider="aws"
            ) from e

    async def create_vpn_gateway(
        self,
        vpc_id: str,
        availability_zones: Set[str],
        asn: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> AwsVpnGateway:
        """Create a Virtual Private Gateway.

        Args:
            vpc_id: ID of the VPC to attach the gateway to
            availability_zones: Set of availability zones
            asn: Optional ASN for BGP
            tags: Optional resource tags

        Returns:
            Created VPN gateway

        Raises:
            VpnGatewayCreationError: If gateway creation fails
        """
        try:
            # Create VPN gateway
            vpn_gateway_params = {
                "Type": "ipsec.1",
                "AmazonSideAsn": asn,
            } if asn else {"Type": "ipsec.1"}

            response = self.ec2_client.create_vpn_gateway(**vpn_gateway_params)
            vpn_gateway_id = response["VpnGateway"]["VpnGatewayId"]

            # Attach to VPC
            self.ec2_client.attach_vpn_gateway(
                VpcId=vpc_id,
                VpnGatewayId=vpn_gateway_id
            )

            # Add tags
            if tags:
                self.ec2_client.create_tags(
                    Resources=[vpn_gateway_id],
                    Tags=[{"Key": k, "Value": v} for k, v in tags.items()]
                )

            return AwsVpnGateway(
                vpn_gateway_id=vpn_gateway_id,
                vpc_id=vpc_id,
                availability_zones=availability_zones,
                asn=asn,
                tags=tags or {}
            )

        except (BotoCoreError, ClientError) as e:
            raise VpnGatewayCreationError(
                f"Failed to create VPN gateway: {str(e)}",
                provider="aws",
                details={
                    "vpc_id": vpc_id,
                    "availability_zones": list(availability_zones),
                    "asn": asn,
                }
            ) from e

    async def delete_vpn_gateway(
        self,
        gateway_id: str,
        vpc_id: Optional[str] = None
    ) -> None:
        """Delete a Virtual Private Gateway.

        Args:
            gateway_id: ID of the VPN gateway to delete
            vpc_id: Optional VPC ID to detach from first

        Raises:
            VpnGatewayNotFoundError: If gateway does not exist
            VpnGatewayDeletionError: If deletion fails
        """
        try:
            # Detach from VPC if specified
            if vpc_id:
                self.ec2_client.detach_vpn_gateway(
                    VpcId=vpc_id,
                    VpnGatewayId=gateway_id
                )

            # Delete gateway
            self.ec2_client.delete_vpn_gateway(VpnGatewayId=gateway_id)

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidVpnGatewayID.NotFound":
                raise VpnGatewayNotFoundError(
                    f"VPN gateway not found: {gateway_id}",
                    gateway_id=gateway_id,
                    provider="aws"
                ) from e
            raise VpnGatewayDeletionError(
                f"Failed to delete VPN gateway: {str(e)}",
                gateway_id=gateway_id,
                provider="aws",
                details={"vpc_id": vpc_id}
            ) from e

    async def get_vpn_gateway(self, gateway_id: str) -> AwsVpnGateway:
        """Get Virtual Private Gateway details.

        Args:
            gateway_id: ID of the VPN gateway

        Returns:
            VPN gateway details

        Raises:
            VpnGatewayNotFoundError: If gateway does not exist
        """
        try:
            response = self.ec2_client.describe_vpn_gateways(
                VpnGatewayIds=[gateway_id]
            )

            if not response["VpnGateways"]:
                raise VpnGatewayNotFoundError(
                    f"VPN gateway not found: {gateway_id}",
                    gateway_id=gateway_id,
                    provider="aws"
                )

            gateway = response["VpnGateways"][0]
            vpc_id = None
            if gateway["VpcAttachments"]:
                vpc_id = gateway["VpcAttachments"][0]["VpcId"]

            return AwsVpnGateway(
                vpn_gateway_id=gateway_id,
                vpc_id=vpc_id,
                availability_zones=set(),  # AWS API doesn't return this
                asn=gateway.get("AmazonSideAsn"),
                tags={t["Key"]: t["Value"] for t in gateway.get("Tags", [])}
            )

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidVpnGatewayID.NotFound":
                raise VpnGatewayNotFoundError(
                    f"VPN gateway not found: {gateway_id}",
                    gateway_id=gateway_id,
                    provider="aws"
                ) from e
            raise AwsError(
                f"Failed to get VPN gateway: {str(e)}",
                aws_error_code=e.response["Error"]["Code"]
            ) from e

    async def create_customer_gateway(
        self,
        ip_address: str,
        bgp_asn: int,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a Customer Gateway.

        Args:
            ip_address: Public IP of the customer gateway
            bgp_asn: BGP ASN for the customer gateway
            tags: Optional resource tags

        Returns:
            ID of created customer gateway

        Raises:
            VpnConnectionCreationError: If creation fails
        """
        try:
            response = self.ec2_client.create_customer_gateway(
                BgpAsn=bgp_asn,
                PublicIp=ip_address,
                Type="ipsec.1"
            )

            gateway_id = response["CustomerGateway"]["CustomerGatewayId"]

            if tags:
                self.ec2_client.create_tags(
                    Resources=[gateway_id],
                    Tags=[{"Key": k, "Value": v} for k, v in tags.items()]
                )

            return gateway_id

        except (BotoCoreError, ClientError) as e:
            raise VpnConnectionCreationError(
                f"Failed to create customer gateway: {str(e)}",
                details={
                    "ip_address": ip_address,
                    "bgp_asn": bgp_asn
                }
            ) from e

    async def delete_customer_gateway(self, gateway_id: str) -> None:
        """Delete a Customer Gateway.

        Args:
            gateway_id: ID of the customer gateway to delete

        Raises:
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            self.ec2_client.delete_customer_gateway(
                CustomerGatewayId=gateway_id
            )

        except ClientError as e:
            if e.response["Error"]["Code"] != "InvalidCustomerGatewayID.NotFound":
                raise VpnConnectionDeletionError(
                    f"Failed to delete customer gateway: {str(e)}",
                    connection_id=gateway_id
                ) from e

    async def create_vpn_connection(
        self,
        vpn_gateway_id: str,
        customer_gateway_id: str,
        tunnels: List[TunnelConfig],
        static_routes: Optional[List[str]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> VpnConnection:
        """Create a VPN Connection.

        Args:
            vpn_gateway_id: ID of the Virtual Private Gateway
            customer_gateway_id: ID of the Customer Gateway
            tunnels: List of tunnel configurations
            static_routes: Optional list of static routes
            tags: Optional resource tags

        Returns:
            Created VPN connection

        Raises:
            VpnConnectionCreationError: If creation fails
        """
        try:
            # Prepare tunnel options
            tunnel_options = []
            for tunnel in tunnels:
                options = {
                    "TunnelInsideCidr": str(tunnel.inside_cidr),
                    "PreSharedKey": tunnel.preshared_key,
                }
                if tunnel.ike_config:
                    options.update({
                        "Phase1LifetimeSeconds": tunnel.ike_config.lifetime_seconds,
                        "IkeVersions": [tunnel.ike_config.version],
                        "Phase1EncryptionAlgorithms": [{"Value": tunnel.ike_config.encryption}],
                        "Phase1IntegrityAlgorithms": [{"Value": tunnel.ike_config.integrity}],
                        "Phase1DHGroupNumbers": [{"Value": tunnel.ike_config.dh_group}],
                    })
                if tunnel.ipsec_config:
                    options.update({
                        "Phase2LifetimeSeconds": tunnel.ipsec_config.lifetime_seconds,
                        "Phase2EncryptionAlgorithms": [{"Value": tunnel.ipsec_config.encryption}],
                        "Phase2IntegrityAlgorithms": [{"Value": tunnel.ipsec_config.integrity}],
                        "Phase2DHGroupNumbers": [{"Value": tunnel.ipsec_config.pfs_group}],
                    })
                tunnel_options.append(options)

            # Create VPN connection
            params = {
                "CustomerGatewayId": customer_gateway_id,
                "Type": "ipsec.1",
                "VpnGatewayId": vpn_gateway_id,
                "Options": {
                    "StaticRoutesOnly": bool(static_routes),
                    "TunnelOptions": tunnel_options
                }
            }

            response = self.ec2_client.create_vpn_connection(**params)
            connection = response["VpnConnection"]

            # Add static routes if specified
            if static_routes:
                for route in static_routes:
                    self.ec2_client.create_vpn_connection_route(
                        VpnConnectionId=connection["VpnConnectionId"],
                        DestinationCidrBlock=route
                    )

            # Add tags
            if tags:
                self.ec2_client.create_tags(
                    Resources=[connection["VpnConnectionId"]],
                    Tags=[{"Key": k, "Value": v} for k, v in tags.items()]
                )

            return await self.get_vpn_connection(connection["VpnConnectionId"])

        except (BotoCoreError, ClientError) as e:
            raise VpnConnectionCreationError(
                f"Failed to create VPN connection: {str(e)}",
                details={
                    "vpn_gateway_id": vpn_gateway_id,
                    "customer_gateway_id": customer_gateway_id,
                }
            ) from e

    async def delete_vpn_connection(self, connection_id: str) -> None:
        """Delete a VPN Connection.

        Args:
            connection_id: ID of the VPN connection to delete

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            self.ec2_client.delete_vpn_connection(
                VpnConnectionId=connection_id
            )

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidVpnConnectionID.NotFound":
                raise VpnConnectionNotFoundError(
                    f"VPN connection not found: {connection_id}",
                    connection_id=connection_id
                ) from e
            raise VpnConnectionDeletionError(
                f"Failed to delete VPN connection: {str(e)}",
                connection_id=connection_id
            ) from e

    async def get_vpn_connection(self, connection_id: str) -> VpnConnection:
        """Get VPN Connection details.

        Args:
            connection_id: ID of the VPN connection

        Returns:
            VPN connection details

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
        """
        try:
            response = self.ec2_client.describe_vpn_connections(
                VpnConnectionIds=[connection_id]
            )

            if not response["VpnConnections"]:
                raise VpnConnectionNotFoundError(
                    f"VPN connection not found: {connection_id}",
                    connection_id=connection_id
                )

            conn = response["VpnConnections"][0]

            # Get associated gateways
            vpn_gateway = await self.get_vpn_gateway(conn["VpnGatewayId"])

            # Parse tunnel configurations
            tunnels = []
            for tunnel in conn["Options"]["TunnelOptions"]:
                tunnels.append(TunnelConfig(
                    inside_cidr=tunnel["TunnelInsideCidr"],
                    preshared_key=tunnel["PreSharedKey"],
                ))

            # Parse routes
            routes = []
            for route in conn.get("Routes", []):
                routes.append(RouteEntry(
                    destination=route["DestinationCidrBlock"],
                    origin=route.get("Source", "static"),
                    state=route["State"].lower()
                ))

            # Parse BGP configuration
            bgp_config = None
            if conn["Options"].get("EnableBgp"):
                bgp_config = BgpConfig(
                    enabled=True,
                    asn=conn["Options"]["BgpAsn"],
                    bgp_peer_ip=conn["Options"].get("BgpPeerIp"),
                    bgp_peer_asn=conn["Options"].get("BgpPeerAsn")
                )

            return VpnConnection(
                id=connection_id,
                name=next((t["Value"] for t in conn.get("Tags", [])
                          if t["Key"] == "Name"), connection_id),
                description=next((t["Value"] for t in conn.get("Tags", [])
                                if t["Key"] == "Description"), None),
                aws_gateway=vpn_gateway,
                azure_gateway=None,  # Will be set by manager
                tunnels=tunnels,
                routes=routes,
                bgp_config=bgp_config,
                status=VpnStatus(conn["State"].lower()),
                tags={t["Key"]: t["Value"] for t in conn.get("Tags", [])}
            )

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidVpnConnectionID.NotFound":
                raise VpnConnectionNotFoundError(
                    f"VPN connection not found: {connection_id}",
                    connection_id=connection_id
                ) from e
            raise AwsError(
                f"Failed to get VPN connection: {str(e)}",
                aws_error_code=e.response["Error"]["Code"]
            ) from e
