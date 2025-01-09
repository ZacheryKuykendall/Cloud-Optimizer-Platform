"""AWS network provider implementation.

This module provides functionality for retrieving AWS network information
and pricing data for VPC, Load Balancers, CloudFront, Route53, etc.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from network_comparison.exceptions import (
    BandwidthError,
    CrossRegionError,
    FeatureNotSupportedError,
    NetworkAvailabilityError,
    PricingError,
    ProviderError,
    ServiceConfigurationError,
    ServiceTypeNotSupportedError,
    ThroughputError,
)
from network_comparison.models import (
    CloudProvider,
    CostComponent,
    LoadBalancerType,
    NetworkOption,
    NetworkServiceType,
    OperationalMetrics,
    PricingTier,
)


logger = logging.getLogger(__name__)


class AwsNetworkProvider:
    """Provider for AWS network information and pricing."""

    # Maps our service types to AWS service values
    SERVICE_TYPE_MAPPING = {
        NetworkServiceType.VPC: "AmazonVPC",
        NetworkServiceType.LOAD_BALANCER: {
            LoadBalancerType.APPLICATION: "ApplicationLoadBalancer",
            LoadBalancerType.NETWORK: "NetworkLoadBalancer",
            LoadBalancerType.GATEWAY: "GatewayLoadBalancer",
        },
        NetworkServiceType.CDN: "AmazonCloudFront",
        NetworkServiceType.DNS: "AmazonRoute53",
        NetworkServiceType.VPN: "AWSVPNGateway",
        NetworkServiceType.TRANSIT: "AWSTransitGateway",
        NetworkServiceType.WAF: "AWSWAFv2",
        NetworkServiceType.DDOS: "AWSShield",
        NetworkServiceType.NAT: "AWSNATGateway",
    }

    # Features by service type
    SERVICE_FEATURES = {
        NetworkServiceType.VPC: {
            "flow-logs", "endpoints", "peering", "ipv6",
            "security-groups", "network-acls"
        },
        NetworkServiceType.LOAD_BALANCER: {
            LoadBalancerType.APPLICATION: {
                "ssl-termination", "path-routing", "host-routing",
                "health-checks", "sticky-sessions", "websockets",
                "http2", "grpc", "fixed-response", "redirect"
            },
            LoadBalderType.NETWORK: {
                "tcp-udp", "tls-termination", "preserve-source-ip",
                "health-checks", "cross-zone", "static-ip"
            },
            LoadBalancerType.GATEWAY: {
                "third-party-appliances", "preserve-source-ip",
                "health-checks", "cross-zone"
            },
        },
        NetworkServiceType.CDN: {
            "ssl", "waf-integration", "field-level-encryption",
            "origin-shield", "real-time-logs", "lambda-edge",
            "custom-ssl", "shield-integration"
        },
        NetworkServiceType.DNS: {
            "health-checks", "traffic-flow", "dnssec",
            "private-zones", "geo-routing", "latency-routing",
            "weighted-routing", "failover-routing"
        },
        NetworkServiceType.VPN: {
            "ipsec", "accelerated", "transit-gateway-attachment",
            "custom-asn", "bgp", "route-propagation"
        },
        NetworkServiceType.TRANSIT: {
            "vpc-attachments", "vpn-attachments", "peering",
            "multicast", "route-tables", "blackhole-routes"
        },
        NetworkServiceType.WAF: {
            "ip-blocking", "rate-limiting", "geo-blocking",
            "custom-rules", "managed-rules", "logging",
            "bot-control", "captcha"
        },
        NetworkServiceType.DDOS: {
            "layer3-protection", "layer4-protection", "layer7-protection",
            "health-checks", "notifications", "reporting"
        },
        NetworkServiceType.NAT: {
            "elastic-ip", "cloudwatch-metrics", "flow-logs",
            "cross-zone-failover"
        },
    }

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str,
    ):
        """Initialize AWS network provider.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region
        """
        self.region = region
        
        # Initialize clients
        self.ec2_client = boto3.client(
            "ec2",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )
        self.elbv2_client = boto3.client(
            "elbv2",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )
        self.cloudfront_client = boto3.client(
            "cloudfront",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name="us-east-1",  # CloudFront is global
        )
        self.route53_client = boto3.client(
            "route53",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name="us-east-1",  # Route53 is global
        )
        self.pricing_client = boto3.client(
            "pricing",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name="us-east-1",  # Pricing API only available in us-east-1
        )

    async def list_network_options(
        self,
        service_type: NetworkServiceType,
        region: Optional[str] = None,
    ) -> List[NetworkOption]:
        """List available AWS network options.

        Args:
            service_type: Network service type
            region: Optional region override

        Returns:
            List of network options

        Raises:
            ServiceTypeNotSupportedError: If service type not supported
            NetworkAvailabilityError: If service not available in region
        """
        try:
            region = region or self.region
            options = []

            if service_type == NetworkServiceType.VPC:
                # VPC options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.VPC,
                        region=region,
                        min_bandwidth_gbps=1,
                        max_bandwidth_gbps=100,
                        features=self.SERVICE_FEATURES[NetworkServiceType.VPC],
                        high_availability=True,
                        cross_region=True,
                    ),
                ])

            elif service_type == NetworkServiceType.LOAD_BALANCER:
                # Load balancer options
                for lb_type, features in self.SERVICE_FEATURES[NetworkServiceType.LOAD_BALANCER].items():
                    options.append(
                        NetworkOption(
                            provider=CloudProvider.AWS,
                            service_type=NetworkServiceType.LOAD_BALANCER,
                            region=region,
                            min_bandwidth_gbps=1,
                            max_bandwidth_gbps=None,  # Auto-scaling
                            min_requests_per_second=1,
                            max_requests_per_second=None,  # Auto-scaling
                            features=features,
                            high_availability=True,
                            cross_region=False,
                            load_balancer_type=lb_type,
                        )
                    )

            elif service_type == NetworkServiceType.CDN:
                # CloudFront options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.CDN,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=None,  # Auto-scaling
                        min_requests_per_second=1,
                        max_requests_per_second=None,  # Auto-scaling
                        features=self.SERVICE_FEATURES[NetworkServiceType.CDN],
                        high_availability=True,
                        cross_region=True,
                    ),
                ])

            elif service_type == NetworkServiceType.DNS:
                # Route53 options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.DNS,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=None,
                        min_requests_per_second=1,
                        max_requests_per_second=None,
                        features=self.SERVICE_FEATURES[NetworkServiceType.DNS],
                        high_availability=True,
                        cross_region=True,
                        dns_type=DnsType.PUBLIC,
                    ),
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.DNS,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=None,
                        min_requests_per_second=1,
                        max_requests_per_second=None,
                        features=self.SERVICE_FEATURES[NetworkServiceType.DNS],
                        high_availability=True,
                        cross_region=False,
                        dns_type=DnsType.PRIVATE,
                    ),
                ])

            elif service_type == NetworkServiceType.VPN:
                # VPN Gateway options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.VPN,
                        region=region,
                        min_bandwidth_gbps=0.5,
                        max_bandwidth_gbps=None,
                        features=self.SERVICE_FEATURES[NetworkServiceType.VPN],
                        high_availability=True,
                        cross_region=True,
                        vpn_type=VpnType.SITE_TO_SITE,
                    ),
                ])

            elif service_type == NetworkServiceType.TRANSIT:
                # Transit Gateway options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.TRANSIT,
                        region=region,
                        min_bandwidth_gbps=1,
                        max_bandwidth_gbps=50,
                        features=self.SERVICE_FEATURES[NetworkServiceType.TRANSIT],
                        high_availability=True,
                        cross_region=True,
                        transit_type=TransitType.HUB_SPOKE,
                    ),
                ])

            elif service_type == NetworkServiceType.WAF:
                # WAF options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.WAF,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=None,
                        min_requests_per_second=1,
                        max_requests_per_second=None,
                        features=self.SERVICE_FEATURES[NetworkServiceType.WAF],
                        high_availability=True,
                        cross_region=True,
                        waf_type=WafType.MANAGED,
                    ),
                ])

            elif service_type == NetworkServiceType.DDOS:
                # Shield options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.DDOS,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=None,
                        features=self.SERVICE_FEATURES[NetworkServiceType.DDOS],
                        high_availability=True,
                        cross_region=True,
                        ddos_type=DdosType.ADVANCED,
                    ),
                ])

            elif service_type == NetworkServiceType.NAT:
                # NAT Gateway options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AWS,
                        service_type=NetworkServiceType.NAT,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=45,
                        features=self.SERVICE_FEATURES[NetworkServiceType.NAT],
                        high_availability=True,
                        cross_region=False,
                        nat_type=NatType.GATEWAY,
                    ),
                ])

            else:
                raise ServiceTypeNotSupportedError(
                    f"Service type {service_type.value} not supported",
                    provider="aws",
                    service_type=service_type.value,
                    region=region,
                    supported_types=[t.value for t in NetworkServiceType],
                )

            return options

        except (BotoCoreError, ClientError) as e:
            raise ProviderError(
                f"Failed to list AWS network options: {str(e)}",
                provider="aws",
                error_code=str(e),
            ) from e

    async def get_service_costs(
        self,
        service_type: NetworkServiceType,
        region: str,
        bandwidth_gbps: float,
        data_transfer_gb: Optional[float] = None,
        requests_per_second: Optional[int] = None,
        high_availability: bool = False,
        cross_region: bool = False,
        load_balancer_type: Optional[LoadBalancerType] = None,
        cdn_type: Optional[CdnType] = None,
        dns_type: Optional[DnsType] = None,
        vpn_type: Optional[VpnType] = None,
        transit_type: Optional[TransitType] = None,
        waf_type: Optional[WafType] = None,
        ddos_type: Optional[DdosType] = None,
        nat_type: Optional[NatType] = None,
    ) -> Dict[str, Any]:
        """Get service costs.

        Args:
            service_type: Network service type
            region: Region
            bandwidth_gbps: Required bandwidth in Gbps
            data_transfer_gb: Optional data transfer in GB
            requests_per_second: Optional requests per second
            high_availability: Whether HA is required
            cross_region: Whether cross-region is required
            load_balancer_type: Optional load balancer type
            cdn_type: Optional CDN type
            dns_type: Optional DNS type
            vpn_type: Optional VPN type
            transit_type: Optional transit type
            waf_type: Optional WAF type
            ddos_type: Optional DDoS type
            nat_type: Optional NAT type

        Returns:
            Dictionary with monthly cost and cost components

        Raises:
            PricingError: If error occurs getting pricing
        """
        try:
            # Get service code and filters
            service_code = self.SERVICE_TYPE_MAPPING[service_type]
            if isinstance(service_code, dict):
                service_code = service_code[load_balancer_type]

            filters = [
                {"Type": "TERM_MATCH", "Field": "location", "Value": region},
            ]

            # Add service-specific filters
            if service_type == NetworkServiceType.LOAD_BALANCER:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "LoadBalancerUsage"},
                ])
            elif service_type == NetworkServiceType.CDN:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "DataTransfer-Out-Bytes"},
                ])
            elif service_type == NetworkServiceType.DNS:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "HostedZone"},
                ])
            elif service_type == NetworkServiceType.VPN:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "VPN-Connection-Hour"},
                ])
            elif service_type == NetworkServiceType.TRANSIT:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "TransitGateway-Hour"},
                ])
            elif service_type == NetworkServiceType.WAF:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "Request"},
                ])
            elif service_type == NetworkServiceType.DDOS:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "ShieldProtection"},
                ])
            elif service_type == NetworkServiceType.NAT:
                filters.extend([
                    {"Type": "TERM_MATCH", "Field": "usagetype", "Value": "NatGateway-Hour"},
                ])

            # Get pricing data
            response = self.pricing_client.get_products(
                ServiceCode=service_code,
                Filters=filters,
            )

            if not response["PriceList"]:
                raise PricingError(
                    f"No pricing found for service type {service_type.value}",
                    provider="aws",
                    region=region,
                    service_type=service_type.value,
                )

            # Parse pricing data
            price_list = response["PriceList"][0]
            terms = price_list["terms"]["OnDemand"]
            rate_code = next(iter(terms))
            price_dimensions = terms[rate_code]["priceDimensions"]
            price_dimension = next(iter(price_dimensions.values()))

            # Calculate costs
            cost_components = []
            monthly_cost = Decimal("0")

            # Base service cost
            base_rate = Decimal(price_dimension["pricePerUnit"]["USD"])
            if service_type in {NetworkServiceType.VPN, NetworkServiceType.TRANSIT, NetworkServiceType.NAT}:
                # Hourly services
                base_cost = base_rate * Decimal("730")  # Average hours per month
            else:
                base_cost = base_rate

            cost_components.append(
                CostComponent(
                    name="Service",
                    monthly_cost=base_cost,
                )
            )
            monthly_cost += base_cost

            # Data transfer costs if applicable
            if data_transfer_gb and service_type in {
                NetworkServiceType.LOAD_BALANCER,
                NetworkServiceType.CDN,
                NetworkServiceType.VPN,
                NetworkServiceType.TRANSIT,
                NetworkServiceType.NAT,
            }:
                transfer_cost = self._calculate_data_transfer_cost(
                    service_type=service_type,
                    region=region,
                    data_transfer_gb=data_transfer_gb,
                )
                cost_components.append(
                    CostComponent(
                        name="Data Transfer",
                        monthly_cost=transfer_cost,
                    )
                )
                monthly_cost += transfer_cost

            # Request costs if applicable
            if requests_per_second and service_type in {
                NetworkServiceType.LOAD_BALANCER,
                NetworkServiceType.CDN,
                NetworkServiceType.DNS,
                NetworkServiceType.WAF,
            }:
                request_cost = self._calculate_request_cost(
                    service_type=service_type,
                    region=region,
                    requests_per_second=requests_per_second,
                )
                cost_components.append(
                    CostComponent(
                        name="Requests",
                        monthly_cost=request_cost,
                    )
                )
                monthly_cost += request_cost

            return {
                "monthly_cost": monthly_cost,
                "cost_components": cost_components,
            }

        except (BotoCoreError, ClientError) as e:
            raise PricingError(
                f"Failed to get AWS service costs: {str(e)}",
                provider="aws",
                region=region,
                service_type=service_type.value,
            ) from e

    def _calculate_data_transfer_cost(
        self,
        service_type: NetworkServiceType,
        region: str,
        data_transfer_gb: float,
    ) -> Decimal:
        """Calculate data transfer costs.

        Args:
            service_type: Network service type
            region: Region
            data_transfer_gb: Data transfer in GB

        Returns:
            Monthly cost for data transfer
        """
        # Get tiered pricing based on service type and region
        tiers = self._get_data_transfer_tiers(service_type, region)
        
        # Calculate cost across tiers
        remaining_gb = Decimal(str(data_transfer_gb))
        total_cost = Decimal("0")

        for tier in tiers:
            tier_size = (
                tier.max_gb - tier.min_gb if tier.max_gb
                else remaining_gb
            )
            tier_usage = min(remaining_gb, tier_size)
            if tier_usage > 0:
                total_cost += tier_usage * tier.price_per_gb
                remaining_gb -= tier_usage
            if remaining_gb <= 0:
                break

        return total_cost

    def _calculate_request_cost(
        self,
        service_type: NetworkServiceType,
        region: str,
        requests_per_second: int,
    ) -> Decimal:
        """Calculate request costs.

        Args:
            service_type: Network service type
            region: Region
            requests_per_second: Requests per second

        Returns:
            Monthly cost for requests
        """
        # Convert requests/second to monthly requests
        monthly_requests = Decimal(str(requests_per_second)) * Decimal("2592000")  # 30 days in seconds
        
        # Get request pricing based on service type and region
        price_per_million = self._get_request_pricing(service_type, region)
        
        return (monthly_requests / Decimal("1000000")) * price_per_million

    def _get_data_transfer_tiers(
        self,
        service_type: NetworkServiceType,
        region: str,
    ) -> List[PricingTier]:
        """Get data transfer pricing tiers.

        Args:
            service_type: Network service type
            region: Region

        Returns:
            List of pricing tiers
        """
        # TODO: Implement actual tier retrieval from pricing API
        # For now, return example tiers
        return [
            PricingTier(
                min_usage=0,
                max_usage=1024,  # 1 TB
                price_per_unit=Decimal("0.09"),
                unit="GB",
            ),
            PricingTier(
                min_usage=1024,
                max_usage=10240,  # 10 TB
                price_per_unit=Decimal("0.085"),
                unit="GB",
            ),
            PricingTier(
                min_usage=10240,
                max_usage=None,
                price_per_unit=Decimal("0.07"),
                unit="GB",
            ),
        ]

    def _get_request_pricing(
        self,
        service_type: NetworkServiceType,
        region: str,
    ) -> Decimal:
        """Get request pricing per million requests.

        Args:
            service_type: Network service type
            region: Region

        Returns:
            Price per million requests
        """
        # TODO: Implement actual pricing retrieval from pricing API
        # For now, return example pricing
        if service_type == NetworkServiceType.LOAD_BALANCER:
            return Decimal("0.025")
        elif service_type == NetworkServiceType.CDN:
            return Decimal("0.01")
        elif service_type == NetworkServiceType.DNS:
            return Decimal("0.40")
        elif service_type == NetworkServiceType.WAF:
            return Decimal("0.60")
        else:
            return Decimal("0")
