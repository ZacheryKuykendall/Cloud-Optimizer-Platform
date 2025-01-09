"""Azure network provider implementation.

This module provides functionality for retrieving Azure network information
and pricing data for VNet, Load Balancers, CDN, DNS, etc.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set

from azure.identity import ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.cdn import CdnManagementClient
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.commerce import UsageManagementClient
from azure.core.exceptions import AzureError

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


class AzureNetworkProvider:
    """Provider for Azure network information and pricing."""

    # Maps our service types to Azure service values
    SERVICE_TYPE_MAPPING = {
        NetworkServiceType.VPC: "Microsoft.Network/virtualNetworks",
        NetworkServiceType.LOAD_BALANCER: {
            LoadBalancerType.APPLICATION: "Microsoft.Network/applicationGateways",
            LoadBalancerType.NETWORK: "Microsoft.Network/loadBalancers",
            LoadBalancerType.GATEWAY: "Microsoft.Network/loadBalancers",
        },
        NetworkServiceType.CDN: "Microsoft.Cdn/profiles",
        NetworkServiceType.DNS: "Microsoft.Network/dnszones",
        NetworkServiceType.VPN: "Microsoft.Network/virtualNetworkGateways",
        NetworkServiceType.TRANSIT: "Microsoft.Network/virtualHubs",
        NetworkServiceType.WAF: "Microsoft.Network/applicationGatewayWebApplicationFirewallPolicies",
        NetworkServiceType.DDOS: "Microsoft.Network/ddosProtectionPlans",
        NetworkServiceType.NAT: "Microsoft.Network/natGateways",
    }

    # Features by service type
    SERVICE_FEATURES = {
        NetworkServiceType.VPC: {
            "service-endpoints", "private-endpoints", "peering",
            "ddos-protection", "network-security-groups",
            "route-tables", "ipv6"
        },
        NetworkServiceType.LOAD_BALANCER: {
            LoadBalancerType.APPLICATION: {
                "ssl-termination", "url-based-routing", "waf",
                "multi-site", "session-affinity", "autoscaling",
                "health-probes", "rewrite-rules", "redirect"
            },
            LoadBalancerType.NETWORK: {
                "tcp-udp", "high-availability", "cross-region",
                "health-probes", "outbound-rules", "floating-ip"
            },
            LoadBalancerType.GATEWAY: {
                "internal-lb", "high-availability", "floating-ip",
                "health-probes", "outbound-rules"
            },
        },
        NetworkServiceType.CDN: {
            "https", "compression", "caching-rules", "geo-filtering",
            "custom-domains", "waf", "rules-engine", "analytics"
        },
        NetworkServiceType.DNS: {
            "alias-records", "caa-records", "dnssec",
            "private-zones", "traffic-manager", "geo-routing",
            "weighted-routing", "priority-routing"
        },
        NetworkServiceType.VPN: {
            "ipsec", "point-to-site", "bgp", "active-active",
            "custom-ipsec-policies", "radius-authentication"
        },
        NetworkServiceType.TRANSIT: {
            "virtual-wan", "hub-routing", "secured-hub",
            "branch-connectivity", "vnet-connectivity"
        },
        NetworkServiceType.WAF: {
            "owasp", "custom-rules", "bot-protection",
            "rate-limiting", "geo-filtering", "managed-rules"
        },
        NetworkServiceType.DDOS: {
            "always-on", "adaptive-tuning", "metrics",
            "attack-analytics", "mitigation-reports"
        },
        NetworkServiceType.NAT: {
            "zone-redundancy", "multiple-subnets", "metrics",
            "idle-timeout", "outbound-rules"
        },
    }

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        subscription_id: str,
        location: str,
    ):
        """Initialize Azure network provider.

        Args:
            tenant_id: Azure tenant ID
            client_id: Azure client ID
            client_secret: Azure client secret
            subscription_id: Azure subscription ID
            location: Azure location
        """
        self.location = location
        self.subscription_id = subscription_id

        # Initialize credentials
        self.credentials = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

        # Initialize clients
        self.network_client = NetworkManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )
        self.cdn_client = CdnManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )
        self.dns_client = DnsManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )
        self.commerce_client = UsageManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )

    async def list_network_options(
        self,
        service_type: NetworkServiceType,
        region: Optional[str] = None,
    ) -> List[NetworkOption]:
        """List available Azure network options.

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
            region = region or self.location
            options = []

            if service_type == NetworkServiceType.VPC:
                # VNet options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AZURE,
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
                            provider=CloudProvider.AZURE,
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
                # CDN options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AZURE,
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
                # DNS options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AZURE,
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
                        provider=CloudProvider.AZURE,
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
                        provider=CloudProvider.AZURE,
                        service_type=NetworkServiceType.VPN,
                        region=region,
                        min_bandwidth_gbps=0.5,
                        max_bandwidth_gbps=10,
                        features=self.SERVICE_FEATURES[NetworkServiceType.VPN],
                        high_availability=True,
                        cross_region=True,
                        vpn_type=VpnType.ROUTE_BASED,
                    ),
                ])

            elif service_type == NetworkServiceType.TRANSIT:
                # Virtual WAN options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AZURE,
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
                        provider=CloudProvider.AZURE,
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
                # DDoS Protection options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AZURE,
                        service_type=NetworkServiceType.DDOS,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=None,
                        features=self.SERVICE_FEATURES[NetworkServiceType.DDOS],
                        high_availability=True,
                        cross_region=True,
                        ddos_type=DdosType.STANDARD,
                    ),
                ])

            elif service_type == NetworkServiceType.NAT:
                # NAT Gateway options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.AZURE,
                        service_type=NetworkServiceType.NAT,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=16,
                        features=self.SERVICE_FEATURES[NetworkServiceType.NAT],
                        high_availability=True,
                        cross_region=False,
                        nat_type=NatType.GATEWAY,
                    ),
                ])

            else:
                raise ServiceTypeNotSupportedError(
                    f"Service type {service_type.value} not supported",
                    provider="azure",
                    service_type=service_type.value,
                    region=region,
                    supported_types=[t.value for t in NetworkServiceType],
                )

            return options

        except AzureError as e:
            raise ProviderError(
                f"Failed to list Azure network options: {str(e)}",
                provider="azure",
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
            # Get rate card info
            rate_card = self.commerce_client.rate_card.get(
                filter=(
                    f"OfferDurableId eq 'MS-AZR-0003P' and "
                    f"Currency eq 'USD' and "
                    f"Locale eq 'en-US' and "
                    f"RegionInfo eq '{region}'"
                )
            )

            # Get service code
            service_code = self.SERVICE_TYPE_MAPPING[service_type]
            if isinstance(service_code, dict):
                service_code = service_code[load_balancer_type]

            # Find matching meter
            meter = None
            for meter_info in rate_card.meters:
                if (
                    meter_info.meter_category == "Networking"
                    and meter_info.resource_name == service_code
                ):
                    meter = meter_info
                    break

            if not meter:
                raise PricingError(
                    f"No pricing found for service type {service_type.value}",
                    provider="azure",
                    region=region,
                    service_type=service_type.value,
                )

            # Calculate costs
            cost_components = []
            monthly_cost = Decimal("0")

            # Base service cost
            base_rate = Decimal(str(meter.meter_rates["0"]))
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

        except AzureError as e:
            raise PricingError(
                f"Failed to get Azure service costs: {str(e)}",
                provider="azure",
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
        # TODO: Implement actual tier retrieval from rate card
        # For now, return example tiers
        return [
            PricingTier(
                min_usage=0,
                max_usage=1024,  # 1 TB
                price_per_unit=Decimal("0.087"),
                unit="GB",
            ),
            PricingTier(
                min_usage=1024,
                max_usage=10240,  # 10 TB
                price_per_unit=Decimal("0.083"),
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
        # TODO: Implement actual pricing retrieval from rate card
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
