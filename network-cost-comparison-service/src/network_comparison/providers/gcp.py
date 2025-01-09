"""GCP network provider implementation.

This module provides functionality for retrieving Google Cloud network information
and pricing data for VPC, Load Balancers, Cloud CDN, Cloud DNS, etc.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set

from google.cloud import compute_v1
from google.cloud import billing_v1
from google.api_core import exceptions as google_exceptions

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


class GcpNetworkProvider:
    """Provider for GCP network information and pricing."""

    # Maps our service types to GCP service values
    SERVICE_TYPE_MAPPING = {
        NetworkServiceType.VPC: "compute.googleapis.com/Network",
        NetworkServiceType.LOAD_BALANCER: {
            LoadBalancerType.APPLICATION: "compute.googleapis.com/HttpLoadBalancer",
            LoadBalancerType.NETWORK: "compute.googleapis.com/NetworkLoadBalancer",
            LoadBalancerType.GATEWAY: "compute.googleapis.com/TargetInstance",
        },
        NetworkServiceType.CDN: "compute.googleapis.com/CloudCDN",
        NetworkServiceType.DNS: "dns.googleapis.com/ManagedZone",
        NetworkServiceType.VPN: "compute.googleapis.com/VpnTunnel",
        NetworkServiceType.TRANSIT: "compute.googleapis.com/Router",
        NetworkServiceType.WAF: "compute.googleapis.com/SecurityPolicy",
        NetworkServiceType.DDOS: "compute.googleapis.com/ArmorPolicy",
        NetworkServiceType.NAT: "compute.googleapis.com/Router",
    }

    # Features by service type
    SERVICE_FEATURES = {
        NetworkServiceType.VPC: {
            "auto-mode", "custom-mode", "shared-vpc", "vpc-peering",
            "firewall-rules", "routes", "flow-logs", "private-services"
        },
        NetworkServiceType.LOAD_BALANCER: {
            LoadBalancerType.APPLICATION: {
                "ssl-termination", "url-maps", "cdn-integration",
                "security-policies", "identity-aware-proxy",
                "cloud-armor", "serverless-neg", "health-checks"
            },
            LoadBalancerType.NETWORK: {
                "tcp-udp", "ssl-proxy", "internal-tcp-udp",
                "preserve-client-ip", "health-checks", "backend-service"
            },
            LoadBalancerType.GATEWAY: {
                "internal-tcp-udp", "preserve-client-ip",
                "health-checks", "backend-service"
            },
        },
        NetworkServiceType.CDN: {
            "ssl", "custom-domains", "cache-invalidation",
            "signed-urls", "compression", "cache-keys",
            "bypass-cache", "request-coalescing"
        },
        NetworkServiceType.DNS: {
            "dnssec", "private-zones", "forwarding",
            "peering", "routing-policies", "cloud-logging",
            "record-sets", "managed-certificates"
        },
        NetworkServiceType.VPN: {
            "ha-vpn", "classic-vpn", "dynamic-routing",
            "static-routing", "cloud-router", "bgp"
        },
        NetworkServiceType.TRANSIT: {
            "bgp", "custom-routes", "route-advertisement",
            "nat", "vpn-tunnels", "interconnect"
        },
        NetworkServiceType.WAF: {
            "preconfigured-rules", "custom-rules", "rate-limiting",
            "geo-blocking", "adaptive-protection", "logging",
            "ddos-protection", "bot-management"
        },
        NetworkServiceType.DDOS: {
            "layer3-protection", "layer4-protection", "layer7-protection",
            "adaptive-protection", "logging", "metrics"
        },
        NetworkServiceType.NAT: {
            "auto-scaling", "manual-scaling", "logging",
            "port-allocation", "static-ip", "drain-timeouts"
        },
    }

    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        credentials_dict: Optional[Dict] = None,
        region: str = "us-central1",
    ):
        """Initialize GCP network provider.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file
            credentials_dict: Service account credentials as dictionary
            region: GCP region
        """
        self.project_id = project_id
        self.region = region

        # Initialize clients
        self.compute_client = compute_v1.ComputeClient()
        self.billing_client = billing_v1.CloudCatalogClient()

    async def list_network_options(
        self,
        service_type: NetworkServiceType,
        region: Optional[str] = None,
    ) -> List[NetworkOption]:
        """List available GCP network options.

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
                        provider=CloudProvider.GCP,
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
                            provider=CloudProvider.GCP,
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
                # Cloud CDN options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.GCP,
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
                # Cloud DNS options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.GCP,
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
                        provider=CloudProvider.GCP,
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
                # Cloud VPN options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.GCP,
                        service_type=NetworkServiceType.VPN,
                        region=region,
                        min_bandwidth_gbps=0.5,
                        max_bandwidth_gbps=3,
                        features=self.SERVICE_FEATURES[NetworkServiceType.VPN],
                        high_availability=True,
                        cross_region=True,
                        vpn_type=VpnType.ROUTE_BASED,
                    ),
                ])

            elif service_type == NetworkServiceType.TRANSIT:
                # Cloud Router options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.GCP,
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
                # Cloud Armor options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.GCP,
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
                # Cloud Armor options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.GCP,
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
                # Cloud NAT options
                options.extend([
                    NetworkOption(
                        provider=CloudProvider.GCP,
                        service_type=NetworkServiceType.NAT,
                        region=region,
                        min_bandwidth_gbps=0.1,
                        max_bandwidth_gbps=32,
                        features=self.SERVICE_FEATURES[NetworkServiceType.NAT],
                        high_availability=True,
                        cross_region=False,
                        nat_type=NatType.GATEWAY,
                    ),
                ])

            else:
                raise ServiceTypeNotSupportedError(
                    f"Service type {service_type.value} not supported",
                    provider="gcp",
                    service_type=service_type.value,
                    region=region,
                    supported_types=[t.value for t in NetworkServiceType],
                )

            return options

        except google_exceptions.GoogleAPIError as e:
            raise ProviderError(
                f"Failed to list GCP network options: {str(e)}",
                provider="gcp",
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
            # Get service code
            service_code = self.SERVICE_TYPE_MAPPING[service_type]
            if isinstance(service_code, dict):
                service_code = service_code[load_balancer_type]

            # Build SKU filter
            filters = [
                f"serviceId:6F81-5844-456A",  # Compute Engine
                f"region:{region}",
            ]

            if service_type == NetworkServiceType.LOAD_BALANCER:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:LoadBalancer",
                    f"description:{service_code}",
                ])
            elif service_type == NetworkServiceType.CDN:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:CDN",
                ])
            elif service_type == NetworkServiceType.DNS:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:DNS",
                ])
            elif service_type == NetworkServiceType.VPN:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:VPN",
                ])
            elif service_type == NetworkServiceType.TRANSIT:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:Router",
                ])
            elif service_type == NetworkServiceType.WAF:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:SecurityPolicy",
                ])
            elif service_type == NetworkServiceType.DDOS:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:ArmorPolicy",
                ])
            elif service_type == NetworkServiceType.NAT:
                filters.extend([
                    f"resourceFamily:Network",
                    f"resourceGroup:Router",
                    f"description:NAT",
                ])

            request = billing_v1.ListSkusRequest(
                parent=f"services/6F81-5844-456A",
                filter=" AND ".join(filters),
            )

            # Get matching SKU
            skus = self.billing_client.list_skus(request=request)
            sku = next(skus, None)

            if not sku:
                raise PricingError(
                    f"No pricing found for service type {service_type.value}",
                    provider="gcp",
                    region=region,
                    service_type=service_type.value,
                )

            # Calculate costs
            cost_components = []
            monthly_cost = Decimal("0")

            # Base service cost
            pricing_info = sku.pricing_info[0]
            price_expression = pricing_info.pricing_expression
            unit_price = price_expression.tiered_rates[0].unit_price

            base_rate = Decimal(str(unit_price.nanos / 1e9))
            if unit_price.units:
                base_rate += Decimal(str(unit_price.units))

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

        except google_exceptions.GoogleAPIError as e:
            raise PricingError(
                f"Failed to get GCP service costs: {str(e)}",
                provider="gcp",
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
        # TODO: Implement actual tier retrieval from billing API
        # For now, return example tiers
        return [
            PricingTier(
                min_usage=0,
                max_usage=1024,  # 1 TB
                price_per_unit=Decimal("0.085"),
                unit="GB",
            ),
            PricingTier(
                min_usage=1024,
                max_usage=10240,  # 10 TB
                price_per_unit=Decimal("0.080"),
                unit="GB",
            ),
            PricingTier(
                min_usage=10240,
                max_usage=None,
                price_per_unit=Decimal("0.065"),
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
        # TODO: Implement actual pricing retrieval from billing API
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
