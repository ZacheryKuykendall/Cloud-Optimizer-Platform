"""Network cost comparison engine.

This module provides the core functionality for comparing network costs
across different cloud providers (AWS, Azure, GCP).
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from cloud_cost_normalization.currency import CurrencyConverter
from network_comparison.exceptions import (
    BandwidthError,
    ComparisonTimeoutError,
    CrossRegionError,
    FeatureNotSupportedError,
    FilterValidationError,
    NetworkAvailabilityError,
    NoMatchingOptionsError,
    PricingError,
    ServiceConfigurationError,
    ServiceTypeNotSupportedError,
    ThroughputError,
    ValidationError,
)
from network_comparison.models import (
    CloudProvider,
    ComparisonFilter,
    ComparisonResult,
    CostComponent,
    NetworkComparison,
    NetworkCostEstimate,
    NetworkOption,
    NetworkRequirements,
    NetworkServiceType,
    OperationalMetrics,
    PricingTier,
)
from network_comparison.providers.aws import AwsNetworkProvider
from network_comparison.providers.azure import AzureNetworkProvider
from network_comparison.providers.gcp import GcpNetworkProvider


logger = logging.getLogger(__name__)


class NetworkComparisonEngine:
    """Engine for comparing network costs across cloud providers."""

    def __init__(
        self,
        aws_provider: AwsNetworkProvider,
        azure_provider: AzureNetworkProvider,
        gcp_provider: GcpNetworkProvider,
        currency_converter: CurrencyConverter,
        cache_ttl_seconds: int = 3600,
        comparison_timeout_seconds: int = 30,
    ):
        """Initialize network comparison engine.

        Args:
            aws_provider: AWS network provider
            azure_provider: Azure network provider
            gcp_provider: GCP network provider
            currency_converter: Currency conversion service
            cache_ttl_seconds: Cache TTL in seconds
            comparison_timeout_seconds: Comparison timeout in seconds
        """
        self.providers = {
            CloudProvider.AWS: aws_provider,
            CloudProvider.AZURE: azure_provider,
            CloudProvider.GCP: gcp_provider,
        }
        self.currency_converter = currency_converter
        self.cache_ttl_seconds = cache_ttl_seconds
        self.comparison_timeout_seconds = comparison_timeout_seconds

    async def compare_network(
        self,
        requirements: NetworkRequirements,
        filters: Optional[ComparisonFilter] = None,
    ) -> ComparisonResult:
        """Compare network costs across providers based on requirements.

        Args:
            requirements: Network requirements
            filters: Optional comparison filters

        Returns:
            Comparison result with cost estimates and recommendations

        Raises:
            ValidationError: If requirements are invalid
            NoMatchingOptionsError: If no options match requirements
            ComparisonTimeoutError: If comparison times out
        """
        start_time = datetime.utcnow()

        # Validate requirements
        self._validate_requirements(requirements)

        # Apply filters
        providers_to_check = self._get_providers_to_check(filters)
        total_options = 0
        filtered_options = 0

        try:
            # Gather matching options from each provider
            tasks = []
            for provider in providers_to_check:
                task = asyncio.create_task(
                    self._get_matching_options(
                        provider=provider,
                        requirements=requirements,
                        filters=filters,
                    )
                )
                tasks.append(task)

            # Wait for all tasks with timeout
            options_by_provider = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=self.comparison_timeout_seconds
            )

            # Calculate costs for matching options
            estimates = []
            for provider_options in options_by_provider:
                if not provider_options:
                    continue
                
                provider = provider_options[0].provider
                total_options += len(provider_options)

                # Get cost estimates
                provider_estimates = await self._get_cost_estimates(
                    provider=provider,
                    options=provider_options,
                    requirements=requirements,
                )
                
                # Apply cost filters
                if filters:
                    provider_estimates = self._apply_cost_filters(
                        estimates=provider_estimates,
                        filters=filters,
                    )
                
                filtered_options += len(provider_estimates)
                estimates.extend(provider_estimates)

            if not estimates:
                raise NoMatchingOptionsError(
                    "No network options match the specified requirements",
                    requirements=requirements.dict(),
                    providers=[p.value for p in providers_to_check],
                    regions=[requirements.region],
                )

            # Find recommended option
            recommended = self._get_recommended_option(
                estimates=estimates,
                requirements=requirements,
            )

            # Create comparison result
            comparison = NetworkComparison(
                requirements=requirements,
                estimates=estimates,
                recommended_option=recommended,
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return ComparisonResult(
                comparison=comparison,
                filters_applied=filters or ComparisonFilter(),
                total_options_considered=total_options,
                filtered_options_count=filtered_options,
                processing_time_ms=processing_time,
                cache_hit=False,  # TODO: Implement caching
            )

        except asyncio.TimeoutError as e:
            raise ComparisonTimeoutError(
                f"Comparison timed out after {self.comparison_timeout_seconds} seconds",
                timeout_seconds=self.comparison_timeout_seconds,
            ) from e

    def _validate_requirements(self, requirements: NetworkRequirements) -> None:
        """Validate network requirements.

        Args:
            requirements: Network requirements to validate

        Raises:
            ValidationError: If requirements are invalid
        """
        # Validate bandwidth
        if requirements.bandwidth_gbps <= 0:
            raise ValidationError(
                "Bandwidth must be greater than 0",
                field="bandwidth_gbps",
                value=requirements.bandwidth_gbps,
                constraints={"min": 0},
            )

        # Validate data transfer if specified
        if requirements.data_transfer_gb is not None and requirements.data_transfer_gb < 0:
            raise ValidationError(
                "Data transfer must be non-negative",
                field="data_transfer_gb",
                value=requirements.data_transfer_gb,
                constraints={"min": 0},
            )

        # Validate requests per second if specified
        if requirements.requests_per_second is not None and requirements.requests_per_second < 0:
            raise ValidationError(
                "Requests per second must be non-negative",
                field="requests_per_second",
                value=requirements.requests_per_second,
                constraints={"min": 0},
            )

        # Validate service-specific requirements
        if requirements.service_type == NetworkServiceType.LOAD_BALANCER and not requirements.load_balancer_type:
            raise ValidationError(
                "Load balancer type is required for load balancer service",
                field="load_balancer_type",
                value=None,
                constraints={"required": True},
            )

        if requirements.service_type == NetworkServiceType.CDN and not requirements.cdn_type:
            raise ValidationError(
                "CDN type is required for CDN service",
                field="cdn_type",
                value=None,
                constraints={"required": True},
            )

        if requirements.service_type == NetworkServiceType.DNS and not requirements.dns_type:
            raise ValidationError(
                "DNS type is required for DNS service",
                field="dns_type",
                value=None,
                constraints={"required": True},
            )

        if requirements.service_type == NetworkServiceType.VPN and not requirements.vpn_type:
            raise ValidationError(
                "VPN type is required for VPN service",
                field="vpn_type",
                value=None,
                constraints={"required": True},
            )

        if requirements.service_type == NetworkServiceType.TRANSIT and not requirements.transit_type:
            raise ValidationError(
                "Transit type is required for transit service",
                field="transit_type",
                value=None,
                constraints={"required": True},
            )

        if requirements.service_type == NetworkServiceType.WAF and not requirements.waf_type:
            raise ValidationError(
                "WAF type is required for WAF service",
                field="waf_type",
                value=None,
                constraints={"required": True},
            )

        if requirements.service_type == NetworkServiceType.DDOS and not requirements.ddos_type:
            raise ValidationError(
                "DDoS type is required for DDoS service",
                field="ddos_type",
                value=None,
                constraints={"required": True},
            )

        if requirements.service_type == NetworkServiceType.NAT and not requirements.nat_type:
            raise ValidationError(
                "NAT type is required for NAT service",
                field="nat_type",
                value=None,
                constraints={"required": True},
            )

    def _get_providers_to_check(
        self,
        filters: Optional[ComparisonFilter]
    ) -> Set[CloudProvider]:
        """Get set of providers to check based on filters.

        Args:
            filters: Optional comparison filters

        Returns:
            Set of providers to check
        """
        if not filters or not filters.providers:
            return set(CloudProvider)
        return filters.providers

    async def _get_matching_options(
        self,
        provider: CloudProvider,
        requirements: NetworkRequirements,
        filters: Optional[ComparisonFilter] = None,
    ) -> List[NetworkOption]:
        """Get matching network options from a provider.

        Args:
            provider: Cloud provider
            requirements: Network requirements
            filters: Optional comparison filters

        Returns:
            List of matching network options

        Raises:
            ServiceTypeNotSupportedError: If service type not supported
            NetworkAvailabilityError: If service not available in region
            FeatureNotSupportedError: If required feature not supported
        """
        provider_client = self.providers[provider]
        
        # Get available options
        options = await provider_client.list_network_options(
            service_type=requirements.service_type,
            region=requirements.region,
        )

        # Filter by requirements
        options = [
            o for o in options
            if (
                o.min_bandwidth_gbps <= requirements.bandwidth_gbps
                and (not o.max_bandwidth_gbps or requirements.bandwidth_gbps <= o.max_bandwidth_gbps)
                and (not requirements.requests_per_second or not o.min_requests_per_second or requirements.requests_per_second >= o.min_requests_per_second)
                and (not requirements.requests_per_second or not o.max_requests_per_second or requirements.requests_per_second <= o.max_requests_per_second)
                and (not requirements.high_availability or o.high_availability)
                and (not requirements.cross_region or o.cross_region)
            )
        ]

        # Filter by required features
        if requirements.required_features:
            options = [
                o for o in options
                if all(f in o.features for f in requirements.required_features)
            ]

        # Filter by required certifications
        if requirements.required_certifications:
            options = [
                o for o in options
                if all(c in o.certifications for c in requirements.required_certifications)
            ]

        # Apply service-specific filters
        if requirements.service_type == NetworkServiceType.LOAD_BALANCER:
            options = [o for o in options if o.load_balancer_type == requirements.load_balancer_type]
        elif requirements.service_type == NetworkServiceType.CDN:
            options = [o for o in options if o.cdn_type == requirements.cdn_type]
        elif requirements.service_type == NetworkServiceType.DNS:
            options = [o for o in options if o.dns_type == requirements.dns_type]
        elif requirements.service_type == NetworkServiceType.VPN:
            options = [o for o in options if o.vpn_type == requirements.vpn_type]
        elif requirements.service_type == NetworkServiceType.TRANSIT:
            options = [o for o in options if o.transit_type == requirements.transit_type]
        elif requirements.service_type == NetworkServiceType.WAF:
            options = [o for o in options if o.waf_type == requirements.waf_type]
        elif requirements.service_type == NetworkServiceType.DDOS:
            options = [o for o in options if o.ddos_type == requirements.ddos_type]
        elif requirements.service_type == NetworkServiceType.NAT:
            options = [o for o in options if o.nat_type == requirements.nat_type]

        # Apply additional filters
        if filters:
            if filters.min_bandwidth_gbps:
                options = [o for o in options if o.min_bandwidth_gbps >= filters.min_bandwidth_gbps]
            if filters.max_bandwidth_gbps:
                options = [o for o in options if not o.max_bandwidth_gbps or o.max_bandwidth_gbps <= filters.max_bandwidth_gbps]
            if filters.min_requests_per_second:
                options = [o for o in options if o.min_requests_per_second and o.min_requests_per_second >= filters.min_requests_per_second]
            if filters.max_requests_per_second:
                options = [o for o in options if not o.max_requests_per_second or o.max_requests_per_second <= filters.max_requests_per_second]
            if filters.high_availability is not None:
                options = [o for o in options if o.high_availability == filters.high_availability]
            if filters.cross_region is not None:
                options = [o for o in options if o.cross_region == filters.cross_region]

        return options

    async def _get_cost_estimates(
        self,
        provider: CloudProvider,
        options: List[NetworkOption],
        requirements: NetworkRequirements,
    ) -> List[NetworkCostEstimate]:
        """Get cost estimates for network options.

        Args:
            provider: Cloud provider
            options: List of network options
            requirements: Network requirements

        Returns:
            List of cost estimates

        Raises:
            PricingError: If error occurs getting pricing
        """
        provider_client = self.providers[provider]
        estimates = []

        for option in options:
            # Get base service costs
            service_costs = await provider_client.get_service_costs(
                service_type=option.service_type,
                region=requirements.region,
                bandwidth_gbps=requirements.bandwidth_gbps,
                data_transfer_gb=requirements.data_transfer_gb,
                requests_per_second=requirements.requests_per_second,
                high_availability=requirements.high_availability,
                cross_region=requirements.cross_region,
                load_balancer_type=requirements.load_balancer_type,
                cdn_type=requirements.cdn_type,
                dns_type=requirements.dns_type,
                vpn_type=requirements.vpn_type,
                transit_type=requirements.transit_type,
                waf_type=requirements.waf_type,
                ddos_type=requirements.ddos_type,
                nat_type=requirements.nat_type,
            )

            # Create cost estimate
            estimate = NetworkCostEstimate(
                provider=provider,
                service_type=option.service_type,
                region=requirements.region,
                bandwidth_gbps=requirements.bandwidth_gbps,
                data_transfer_gb=requirements.data_transfer_gb,
                requests_per_second=requirements.requests_per_second,
                monthly_cost=service_costs.monthly_cost,
                cost_components=service_costs.cost_components,
                features=option.features,
                load_balancer_type=option.load_balancer_type,
                cdn_type=option.cdn_type,
                dns_type=option.dns_type,
                vpn_type=option.vpn_type,
                transit_type=option.transit_type,
                waf_type=option.waf_type,
                ddos_type=option.ddos_type,
                nat_type=option.nat_type,
            )

            estimates.append(estimate)

        return estimates

    def _apply_cost_filters(
        self,
        estimates: List[NetworkCostEstimate],
        filters: ComparisonFilter,
    ) -> List[NetworkCostEstimate]:
        """Apply cost filters to estimates.

        Args:
            estimates: List of cost estimates
            filters: Comparison filters

        Returns:
            Filtered list of estimates
        """
        if filters.max_monthly_cost:
            estimates = [
                e for e in estimates
                if e.monthly_cost <= filters.max_monthly_cost
            ]

        return estimates

    def _get_recommended_option(
        self,
        estimates: List[NetworkCostEstimate],
        requirements: NetworkRequirements,
    ) -> NetworkCostEstimate:
        """Get recommended option from estimates.

        Args:
            estimates: List of cost estimates
            requirements: Network requirements

        Returns:
            Recommended cost estimate
        """
        # For now, simply return lowest cost option
        # TODO: Consider performance, reliability, etc.
        return min(estimates, key=lambda e: e.monthly_cost)
