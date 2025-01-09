"""AWS client for VPN operations.

This module provides a client for managing AWS VPN resources including
Virtual Private Gateways, Customer Gateways, and VPN Connections.
"""

import logging
from typing import Dict, List, Optional, Set

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from cloud_network_manager.vpn_modules.aws_gcp.exceptions import (
    AuthenticationError,
    AwsError,
    ValidationError,
    VpnConnectionCreationError,
    VpnConnectionDeletionError,
    VpnConnectionNotFoundError,
    VpnGatewayCreationError,
    VpnGatewayDeletionError,
    VpnGatewayNotFoundError,
)
from cloud_network_manager.vpn_modules.aws_gcp.models import (
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
    ):
        """Initialize AWS VPN client.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region

        Raises:
            AuthenticationError: If AWS credentials are invalid
        """
        try:
            self.region = region
            self.ec2_client = boto3.client(
                "ec2",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region,
            )

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
            vpc_id: VPC ID to attach gateway to
            availability_zones: Set of availability zones
            asn: Optional ASN for BGP
            tags: Optional resource tags

        Returns:
            Created VPN gateway

        Raises:
            VpnGatewayCreationError: If gateway creation fails
        """
        try:
            # Create gateway
            gateway = self.ec2_client.create_vpn_gateway(
                Type="ipsec.1",
                AmazonSideAsn=asn,
                TagSpecifications=[{
                    "ResourceType": "vpn-gateway",
                    "Tags": [{"Key": k, "Value": v} for k, v in (tags or {}).items()]
                }]
            )["VpnGateway"]

            # Attach to VPC
            self.ec2_client.attach_vpn_gateway(
                VpcId=vpc_id,
                VpnGatewayId=gateway["VpnGatewayId"]
            )

            return AwsVpnGateway(
                vpn_gateway_id=gateway["VpnGatewayId"],
                vpc_id=vpc_id,
                availability_zones=availability_zones,
                state=gateway["State"],
                amazon_side_asn=asn,
                tags=tags or {}
            )

        except (BotoCoreError, ClientError) as e:
            raise VpnGatewayCreationError(
                f"Failed to create VPN gateway: {str(e)}",
                provider="aws",
                details={
                    "vpc_id": vpc_id,
                    "availability_zones": list(availability_zones),
                }
            ) from e

    async def delete_vpn_gateway(
        self,
        gateway_id: str,
        vpc_id: str
    ) -> None:
        """Delete a Virtual Private Gateway.

        Args:
            gateway_id: Gateway ID
            vpc_id: VPC ID gateway is attached to

        Raises:
            VpnGatewayNotFoundError: If gateway does not exist
            VpnGatewayDeletionError: If deletion fails
        """
        try:
            # Detach from VPC
            self.ec2_client.detach_vpn_gateway(
                VpcId=vpc_id,
                VpnGatewayId=gateway_id
            )

            # Delete gateway
            self.ec2_client.delete_vpn_gateway(
                VpnGatewayId=gateway_id
            )

        except (BotoCoreError, ClientError) as e:
            if "does not exist" in str(e):
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

    async def get_vpn_gateway(
        self,
        gateway_id: str
    ) -> AwsVpnGateway:
        """Get Virtual Private Gateway details.

        Args:
            gateway_id: Gateway ID

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
            vpc_id = gateway["VpcAttachments"][0]["VpcId"] if gateway["VpcAttachments"] else None

            return AwsVpnGateway(
                vpn_gateway_id=gateway["VpnGatewayId"],
                vpc_id=vpc_id,
                availability_zones=set(),  # Not exposed by AWS API
                state=gateway["State"],
                amazon_side_asn=gateway.get("AmazonSideAsn"),
                tags={t["Key"]: t["Value"] for t in gateway.get("Tags", [])}
            )

        except (BotoCoreError, ClientError) as e:
            if "does not exist" in str(e):
                raise VpnGatewayNotFoundError(
                    f"VPN gateway not found: {gateway_id}",
                    gateway_id=gateway_id,
                    provider="aws"
                ) from e
            raise AwsError(
                f"Failed to get VPN gateway: {str(e)}",
                aws_error_code=str(e)
            ) from e

    async def create_customer_gateway(
        self,
        ip_address: str,
        bgp_asn: int,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a Customer Gateway.

        Args:
            ip_address: Public IP of the GCP VPN gateway
            bgp_asn: BGP ASN
            tags: Optional resource tags

        Returns:
            ID of created customer gateway

        Raises:
            VpnConnectionCreationError: If creation fails
        """
        try:
            gateway = self.ec2_client.create_customer_gateway(
                Type="ipsec.1",
                PublicIp=ip_address,
                BgpAsn=bgp_asn,
                TagSpecifications=[{
                    "ResourceType": "customer-gateway",
                    "Tags": [{"Key": k, "Value": v} for k, v in (tags or {}).items()]
                }]
            )["CustomerGateway"]

            return gateway["CustomerGatewayId"]

        except (BotoCoreError, ClientError) as e:
            raise VpnConnectionCreationError(
                f"Failed to create customer gateway: {str(e)}",
                details={
                    "ip_address": ip_address,
                    "bgp_asn": bgp_asn,
                }
            ) from e

    async def delete_customer_gateway(
        self,
        gateway_id: str
    ) -> None:
        """Delete a Customer Gateway.

        Args:
            gateway_id: Gateway ID

        Raises:
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            self.ec2_client.delete_customer_gateway(
                CustomerGatewayId=gateway_id
            )

        except (BotoCoreError, ClientError) as e:
            if "does not exist" not in str(e):
                raise VpnConnectionDeletionError(
                    f"Failed to delete customer gateway: {str(e)}",
                    connection_id=gateway_id
                ) from e

    async def create_vpn_connection(
        self,
        vpn_gateway_id: str,
        customer_gateway_id: str,
        tunnels: List[TunnelConfig],
        tags: Optional[Dict[str, str]] = None
    ) -> VpnConnection:
        """Create a VPN Connection.

        Args:
            vpn_gateway_id: Virtual Private Gateway ID
            customer_gateway_id: Customer Gateway ID
            tunnels: List of tunnel configurations
            tags: Optional resource tags

        Returns:
            Created VPN connection

        Raises:
            VpnConnectionCreationError: If creation fails
        """
        try:
            # Validate tunnel count
            if len(tunnels) not in (1, 2):
                raise ValidationError(
                    "Must specify either 1 or 2 tunnels"
                )

            # Create connection
            connection = self.ec2_client.create_vpn_connection(
                Type="ipsec.1",
                CustomerGatewayId=customer_gateway_id,
                VpnGatewayId=vpn_gateway_id,
                Options={
                    "StaticRoutesOnly": False,  # Enable BGP
                    "TunnelOptions": [{
                        "PreSharedKey": tunnel.preshared_key,
                        "TunnelInsideCidr": str(tunnel.inside_cidr)
                    } for tunnel in tunnels]
                },
                TagSpecifications=[{
                    "ResourceType": "vpn-connection",
                    "Tags": [{"Key": k, "Value": v} for k, v in (tags or {}).items()]
                }]
            )["VpnConnection"]

            # Get full connection details
            return await self.get_vpn_connection(connection["VpnConnectionId"])

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise VpnConnectionCreationError(
                f"Failed to create VPN connection: {str(e)}",
                details={
                    "vpn_gateway_id": vpn_gateway_id,
                    "customer_gateway_id": customer_gateway_id,
                }
            ) from e

    async def delete_vpn_connection(
        self,
        connection_id: str
    ) -> None:
        """Delete a VPN Connection.

        Args:
            connection_id: Connection ID

        Raises:
            VpnConnectionNotFoundError: If connection does not exist
            VpnConnectionDeletionError: If deletion fails
        """
        try:
            self.ec2_client.delete_vpn_connection(
                VpnConnectionId=connection_id
            )

        except (BotoCoreError, ClientError) as e:
            if "does not exist" in str(e):
                raise VpnConnectionNotFoundError(
                    f"VPN connection not found: {connection_id}",
                    connection_id=connection_id
                ) from e
            raise VpnConnectionDeletionError(
                f"Failed to delete VPN connection: {str(e)}",
                connection_id=connection_id
            ) from e

    async def get_vpn_connection(
        self,
        connection_id: str
    ) -> VpnConnection:
        """Get VPN Connection details.

        Args:
            connection_id: Connection ID

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

            connection = response["VpnConnections"][0]

            # Get associated gateways
            vpn_gateway = await self.get_vpn_gateway(connection["VpnGatewayId"])

            # Parse tunnel configurations
            tunnels = []
            for tunnel in connection["Options"]["TunnelOptions"]:
                tunnels.append(TunnelConfig(
                    inside_cidr=tunnel["TunnelInsideCidr"],
                    preshared_key=tunnel["PreSharedKey"],
                ))

            # Parse routes
            routes = []
            for route in connection.get("Routes", []):
                routes.append(RouteEntry(
                    destination=route["DestinationCidrBlock"],
                    next_hop=None,  # AWS doesn't expose this
                    origin="static" if route["Static"] else "bgp",
                    state=route["State"].lower(),
                ))

            # Parse BGP configuration
            bgp_config = None
            if not connection["Options"]["StaticRoutesOnly"]:
                bgp_config = BgpConfig(
                    enabled=True,
                    asn=vpn_gateway.amazon_side_asn,
                    bgp_peer_ip=connection["CustomerGatewayConfiguration"]["BgpPeerIp"],
                    bgp_peer_asn=connection["CustomerGatewayConfiguration"]["BgpAsn"]
                )

            return VpnConnection(
                id=connection["VpnConnectionId"],
                name=next((t["Value"] for t in connection.get("Tags", []) if t["Key"] == "Name"), None),
                description=next((t["Value"] for t in connection.get("Tags", []) if t["Key"] == "Description"), None),
                aws_gateway=vpn_gateway,
                gcp_gateway=None,  # Will be set by manager
                tunnels=tunnels,
                routes=routes,
                bgp_config=bgp_config,
                status=VpnStatus(connection["State"].lower()),
                labels={t["Key"]: t["Value"] for t in connection.get("Tags", [])}  # Use labels for GCP compatibility
            )

        except (BotoCoreError, ClientError) as e:
            if "does not exist" in str(e):
                raise VpnConnectionNotFoundError(
                    f"VPN connection not found: {connection_id}",
                    connection_id=connection_id
                ) from e
            raise AwsError(
                f"Failed to get VPN connection: {str(e)}",
                aws_error_code=str(e)
            ) from e
