"""VM cost comparison engine.

This module provides the core functionality for comparing virtual machine costs
across different cloud providers (AWS, Azure, GCP).
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from cloud_cost_normalization.currency import CurrencyConverter
from vm_comparison.exceptions import (
    ComparisonTimeoutError,
    FeatureNotSupportedError,
    FilterValidationError,
    NoMatchingInstancesError,
    PricingError,
    ValidationError,
)
from vm_comparison.models import (
    CloudProvider,
    ComparisonFilter,
    ComparisonResult,
    CostComponent,
    OperatingSystem,
    PurchaseOption,
    VmComparison,
    VmCostEstimate,
    VmInstanceType,
    VmRequirements,
    VmSize,
)
from vm_comparison.providers.aws import AwsVmProvider
from vm_comparison.providers.azure import AzureVmProvider
from vm_comparison.providers.gcp import GcpVmProvider


logger = logging.getLogger(__name__)


class VmComparisonEngine:
    """Engine for comparing VM costs across cloud providers."""

    def __init__(
        self,
        aws_provider: AwsVmProvider,
        azure_provider: AzureVmProvider,
        gcp_provider: GcpVmProvider,
        currency_converter: CurrencyConverter,
        cache_ttl_seconds: int = 3600,
        comparison_timeout_seconds: int = 30,
    ):
        """Initialize VM comparison engine.

        Args:
            aws_provider: AWS VM provider
            azure_provider: Azure VM provider
            gcp_provider: GCP VM provider
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

    async def compare_vms(
        self,
        requirements: VmRequirements,
        filters: Optional[ComparisonFilter] = None,
    ) -> ComparisonResult:
        """Compare VM costs across providers based on requirements.

        Args:
            requirements: VM requirements
            filters: Optional comparison filters

        Returns:
            Comparison result with cost estimates and recommendations

        Raises:
            ValidationError: If requirements are invalid
            NoMatchingInstancesError: If no instances match requirements
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
            # Gather matching instances from each provider
            tasks = []
            for provider in providers_to_check:
                task = asyncio.create_task(
                    self._get_matching_instances(
                        provider=provider,
                        requirements=requirements,
                        filters=filters,
                    )
                )
                tasks.append(task)

            # Wait for all tasks with timeout
            instances_by_provider = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=self.comparison_timeout_seconds
            )

            # Calculate costs for matching instances
            estimates = []
            for provider_instances in instances_by_provider:
                if not provider_instances:
                    continue
                
                provider = provider_instances[0].provider
                total_options += len(provider_instances)

                # Get cost estimates
                provider_estimates = await self._get_cost_estimates(
                    provider=provider,
                    instances=provider_instances,
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
                raise NoMatchingInstancesError(
                    "No instances match the specified requirements",
                    requirements=requirements.dict(),
                    providers=[p.value for p in providers_to_check],
                    regions=[requirements.region],
                )

            # Find recommended option
            recommended = self._get_recommended_option(estimates)

            # Create comparison result
            comparison = VmComparison(
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

    def _validate_requirements(self, requirements: VmRequirements) -> None:
        """Validate VM requirements.

        Args:
            requirements: VM requirements to validate

        Raises:
            ValidationError: If requirements are invalid
        """
        # Validate size requirements
        if requirements.size.vcpus < 1:
            raise ValidationError(
                "vCPUs must be at least 1",
                field="size.vcpus",
                value=requirements.size.vcpus,
                constraints={"min": 1},
            )

        if requirements.size.memory_gb < 0.5:
            raise ValidationError(
                "Memory must be at least 0.5 GB",
                field="size.memory_gb",
                value=requirements.size.memory_gb,
                constraints={"min": 0.5},
            )

        # Validate GPU requirements
        if requirements.size.gpu_count and requirements.size.gpu_count < 0:
            raise ValidationError(
                "GPU count must be non-negative",
                field="size.gpu_count",
                value=requirements.size.gpu_count,
                constraints={"min": 0},
            )

        # Validate storage requirements
        if requirements.size.local_disk_gb and requirements.size.local_disk_gb < 0:
            raise ValidationError(
                "Local disk size must be non-negative",
                field="size.local_disk_gb",
                value=requirements.size.local_disk_gb,
                constraints={"min": 0},
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

    async def _get_matching_instances(
        self,
        provider: CloudProvider,
        requirements: VmRequirements,
        filters: Optional[ComparisonFilter] = None,
    ) -> List[VmInstanceType]:
        """Get matching instances from a provider.

        Args:
            provider: Cloud provider
            requirements: VM requirements
            filters: Optional comparison filters

        Returns:
            List of matching instance types

        Raises:
            FeatureNotSupportedError: If required feature is not supported
        """
        provider_client = self.providers[provider]
        
        # Get available instances
        instances = await provider_client.list_instance_types(
            region=requirements.region
        )

        # Filter by size requirements
        instances = [
            i for i in instances
            if i.vcpus >= requirements.size.vcpus
            and i.memory_gb >= requirements.size.memory_gb
            and (not requirements.size.gpu_count or i.gpu_count >= requirements.size.gpu_count)
            and (not requirements.size.local_disk_gb or i.local_disk_gb >= requirements.size.local_disk_gb)
        ]

        # Filter by required features
        if requirements.required_features:
            instances = [
                i for i in instances
                if all(f in i.features for f in requirements.required_features)
            ]

        # Filter by required certifications
        if requirements.required_certifications:
            instances = [
                i for i in instances
                if all(c in i.certifications for c in requirements.required_certifications)
            ]

        # Apply additional filters
        if filters:
            if filters.min_vcpus:
                instances = [i for i in instances if i.vcpus >= filters.min_vcpus]
            if filters.max_vcpus:
                instances = [i for i in instances if i.vcpus <= filters.max_vcpus]
            if filters.min_memory_gb:
                instances = [i for i in instances if i.memory_gb >= filters.min_memory_gb]
            if filters.max_memory_gb:
                instances = [i for i in instances if i.memory_gb <= filters.max_memory_gb]

        return instances

    async def _get_cost_estimates(
        self,
        provider: CloudProvider,
        instances: List[VmInstanceType],
        requirements: VmRequirements,
    ) -> List[VmCostEstimate]:
        """Get cost estimates for instances.

        Args:
            provider: Cloud provider
            instances: List of instance types
            requirements: VM requirements

        Returns:
            List of cost estimates

        Raises:
            PricingError: If error occurs getting pricing
        """
        provider_client = self.providers[provider]
        estimates = []

        for instance in instances:
            # Get base compute costs
            compute_costs = await provider_client.get_compute_costs(
                instance_type=instance.instance_type,
                region=requirements.region,
                operating_system=requirements.operating_system,
                purchase_option=requirements.purchase_option,
            )

            # Get additional cost components
            components = [
                CostComponent(
                    name="Compute",
                    hourly_cost=compute_costs.hourly_cost,
                    monthly_cost=compute_costs.monthly_cost,
                )
            ]

            if instance.local_disk_gb:
                storage_costs = await provider_client.get_storage_costs(
                    instance_type=instance.instance_type,
                    region=requirements.region,
                    storage_gb=instance.local_disk_gb,
                )
                components.append(
                    CostComponent(
                        name="Storage",
                        hourly_cost=storage_costs.hourly_cost,
                        monthly_cost=storage_costs.monthly_cost,
                    )
                )

            # Create cost estimate
            estimate = VmCostEstimate(
                provider=provider,
                region=requirements.region,
                instance_type=instance.instance_type,
                operating_system=requirements.operating_system,
                purchase_option=requirements.purchase_option,
                hourly_cost=sum(c.hourly_cost for c in components),
                monthly_cost=sum(c.monthly_cost for c in components),
                cost_components=components,
            )

            estimates.append(estimate)

        return estimates

    def _apply_cost_filters(
        self,
        estimates: List[VmCostEstimate],
        filters: ComparisonFilter,
    ) -> List[VmCostEstimate]:
        """Apply cost filters to estimates.

        Args:
            estimates: List of cost estimates
            filters: Comparison filters

        Returns:
            Filtered list of estimates
        """
        if filters.max_hourly_cost:
            estimates = [
                e for e in estimates
                if e.hourly_cost <= filters.max_hourly_cost
            ]

        if filters.max_monthly_cost:
            estimates = [
                e for e in estimates
                if e.monthly_cost <= filters.max_monthly_cost
            ]

        return estimates

    def _get_recommended_option(
        self,
        estimates: List[VmCostEstimate]
    ) -> VmCostEstimate:
        """Get recommended option from estimates.

        Args:
            estimates: List of cost estimates

        Returns:
            Recommended cost estimate
        """
        # For now, simply return lowest cost option
        return min(estimates, key=lambda e: e.monthly_cost)
