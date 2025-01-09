"""Storage cost comparison engine.

This module provides the core functionality for comparing storage costs
across different cloud providers (AWS, Azure, GCP).
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from cloud_cost_normalization.currency import CurrencyConverter
from storage_comparison.exceptions import (
    CapacityError,
    ComparisonTimeoutError,
    FeatureNotSupportedError,
    FilterValidationError,
    NoMatchingOptionsError,
    PerformanceError,
    PerformanceTierNotSupportedError,
    PricingError,
    ReplicationNotSupportedError,
    StorageClassNotSupportedError,
    ValidationError,
)
from storage_comparison.models import (
    AccessTier,
    CloudProvider,
    ComparisonFilter,
    ComparisonResult,
    CostComponent,
    OperationalMetrics,
    PerformanceTier,
    PricingTier,
    ReplicationType,
    StorageClass,
    StorageComparison,
    StorageCostEstimate,
    StorageOption,
    StorageRequirements,
    StorageType,
)
from storage_comparison.providers.aws import AwsStorageProvider
from storage_comparison.providers.azure import AzureStorageProvider
from storage_comparison.providers.gcp import GcpStorageProvider


logger = logging.getLogger(__name__)


class StorageComparisonEngine:
    """Engine for comparing storage costs across cloud providers."""

    def __init__(
        self,
        aws_provider: AwsStorageProvider,
        azure_provider: AzureStorageProvider,
        gcp_provider: GcpStorageProvider,
        currency_converter: CurrencyConverter,
        cache_ttl_seconds: int = 3600,
        comparison_timeout_seconds: int = 30,
    ):
        """Initialize storage comparison engine.

        Args:
            aws_provider: AWS storage provider
            azure_provider: Azure storage provider
            gcp_provider: GCP storage provider
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

    async def compare_storage(
        self,
        requirements: StorageRequirements,
        filters: Optional[ComparisonFilter] = None,
    ) -> ComparisonResult:
        """Compare storage costs across providers based on requirements.

        Args:
            requirements: Storage requirements
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
                    "No storage options match the specified requirements",
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
            comparison = StorageComparison(
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

    def _validate_requirements(self, requirements: StorageRequirements) -> None:
        """Validate storage requirements.

        Args:
            requirements: Storage requirements to validate

        Raises:
            ValidationError: If requirements are invalid
        """
        # Validate capacity
        if requirements.capacity_gb <= 0:
            raise ValidationError(
                "Capacity must be greater than 0",
                field="capacity_gb",
                value=requirements.capacity_gb,
                constraints={"min": 0},
            )

        # Validate IOPS if specified
        if requirements.iops is not None and requirements.iops <= 0:
            raise ValidationError(
                "IOPS must be greater than 0",
                field="iops",
                value=requirements.iops,
                constraints={"min": 0},
            )

        # Validate throughput if specified
        if requirements.throughput_mbps is not None and requirements.throughput_mbps <= 0:
            raise ValidationError(
                "Throughput must be greater than 0",
                field="throughput_mbps",
                value=requirements.throughput_mbps,
                constraints={"min": 0},
            )

        # Validate performance tier for block storage
        if (
            requirements.storage_type == StorageType.BLOCK
            and requirements.performance_tier is None
        ):
            raise ValidationError(
                "Performance tier is required for block storage",
                field="performance_tier",
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
        requirements: StorageRequirements,
        filters: Optional[ComparisonFilter] = None,
    ) -> List[StorageOption]:
        """Get matching storage options from a provider.

        Args:
            provider: Cloud provider
            requirements: Storage requirements
            filters: Optional comparison filters

        Returns:
            List of matching storage options

        Raises:
            StorageClassNotSupportedError: If storage class not supported
            PerformanceTierNotSupportedError: If performance tier not supported
            ReplicationNotSupportedError: If replication type not supported
            FeatureNotSupportedError: If required feature not supported
        """
        provider_client = self.providers[provider]
        
        # Get available options
        options = await provider_client.list_storage_options(
            storage_type=requirements.storage_type,
            region=requirements.region,
        )

        # Filter by requirements
        options = [
            o for o in options
            if (
                o.min_capacity_gb <= requirements.capacity_gb
                and (not o.max_capacity_gb or requirements.capacity_gb <= o.max_capacity_gb)
                and (not requirements.iops or not o.min_iops or requirements.iops >= o.min_iops)
                and (not requirements.iops or not o.max_iops or requirements.iops <= o.max_iops)
                and (not requirements.throughput_mbps or not o.min_throughput_mbps or requirements.throughput_mbps >= o.min_throughput_mbps)
                and (not requirements.throughput_mbps or not o.max_throughput_mbps or requirements.throughput_mbps <= o.max_throughput_mbps)
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

        # Apply additional filters
        if filters:
            if filters.storage_classes:
                options = [o for o in options if o.storage_class in filters.storage_classes]
            if filters.replication_types:
                options = [o for o in options if o.replication_type in filters.replication_types]
            if filters.min_capacity_gb:
                options = [o for o in options if o.min_capacity_gb >= filters.min_capacity_gb]
            if filters.max_capacity_gb:
                options = [o for o in options if not o.max_capacity_gb or o.max_capacity_gb <= filters.max_capacity_gb]

        return options

    async def _get_cost_estimates(
        self,
        provider: CloudProvider,
        options: List[StorageOption],
        requirements: StorageRequirements,
    ) -> List[StorageCostEstimate]:
        """Get cost estimates for storage options.

        Args:
            provider: Cloud provider
            options: List of storage options
            requirements: Storage requirements

        Returns:
            List of cost estimates

        Raises:
            PricingError: If error occurs getting pricing
        """
        provider_client = self.providers[provider]
        estimates = []

        for option in options:
            # Get base storage costs
            storage_costs = await provider_client.get_storage_costs(
                storage_type=option.storage_type,
                storage_class=option.storage_class,
                replication_type=option.replication_type,
                region=requirements.region,
                capacity_gb=requirements.capacity_gb,
            )

            # Get additional cost components
            components = [
                CostComponent(
                    name="Storage",
                    monthly_cost=storage_costs.monthly_cost,
                )
            ]

            if requirements.iops:
                iops_costs = await provider_client.get_iops_costs(
                    storage_type=option.storage_type,
                    storage_class=option.storage_class,
                    region=requirements.region,
                    iops=requirements.iops,
                )
                components.append(
                    CostComponent(
                        name="IOPS",
                        monthly_cost=iops_costs.monthly_cost,
                    )
                )

            if requirements.throughput_mbps:
                throughput_costs = await provider_client.get_throughput_costs(
                    storage_type=option.storage_type,
                    storage_class=option.storage_class,
                    region=requirements.region,
                    throughput_mbps=requirements.throughput_mbps,
                )
                components.append(
                    CostComponent(
                        name="Throughput",
                        monthly_cost=throughput_costs.monthly_cost,
                    )
                )

            # Create cost estimate
            estimate = StorageCostEstimate(
                provider=provider,
                storage_type=option.storage_type,
                storage_class=option.storage_class,
                replication_type=option.replication_type,
                region=requirements.region,
                capacity_gb=requirements.capacity_gb,
                monthly_cost=sum(c.monthly_cost for c in components),
                cost_components=components,
                features=option.features,
            )

            estimates.append(estimate)

        return estimates

    def _apply_cost_filters(
        self,
        estimates: List[StorageCostEstimate],
        filters: ComparisonFilter,
    ) -> List[StorageCostEstimate]:
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
        estimates: List[StorageCostEstimate],
        requirements: StorageRequirements,
    ) -> StorageCostEstimate:
        """Get recommended option from estimates.

        Args:
            estimates: List of cost estimates
            requirements: Storage requirements

        Returns:
            Recommended cost estimate
        """
        # For now, simply return lowest cost option
        # TODO: Consider performance, durability, etc.
        return min(estimates, key=lambda e: e.monthly_cost)
