"""Terraform cost analyzer.

This module provides the main analyzer class that integrates the parser
with cloud provider pricing APIs to estimate infrastructure costs.
"""

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from aws_cost_explorer import AWSCostExplorerClient
from azure_cost_management import AzureCostManagementClient
from gcp_billing import GCPBillingClient

from terraform_cost_analyzer.exceptions import (
    ConfigurationError,
    PricingCalculationError,
    PricingDataNotFoundError,
    ValidationError,
)
from terraform_cost_analyzer.models import (
    CloudProvider,
    CostAnalysis,
    CostBreakdown,
    CostComponent,
    CostSummary,
    ModuleCost,
    PricingData,
    ResourceAction,
    ResourceCost,
    ResourceMetadata,
    ResourceType,
)
from terraform_cost_analyzer.parser import TerraformPlanParser

logger = logging.getLogger(__name__)


class TerraformCostAnalyzer:
    """Analyzer for estimating costs of Terraform infrastructure."""

    def __init__(
        self,
        providers: Optional[List[CloudProvider]] = None,
        aws_client: Optional[AWSCostExplorerClient] = None,
        azure_client: Optional[AzureCostManagementClient] = None,
        gcp_client: Optional[GCPBillingClient] = None,
        default_currency: str = "USD",
    ):
        """Initialize the analyzer.

        Args:
            providers: List of cloud providers to support. Defaults to all.
            aws_client: Optional AWS Cost Explorer client.
            azure_client: Optional Azure Cost Management client.
            gcp_client: Optional GCP Billing client.
            default_currency: Default currency for cost estimates.
        """
        self.providers = set(providers) if providers else set(CloudProvider)
        self.default_currency = default_currency.upper()
        self.parser = TerraformPlanParser()

        # Initialize provider clients
        self.aws_client = aws_client
        self.azure_client = azure_client
        self.gcp_client = gcp_client

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate analyzer configuration.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        # Check provider clients
        if CloudProvider.AWS in self.providers and not self.aws_client:
            raise ConfigurationError(
                "AWS client required but not configured",
                config_key="aws_client"
            )
        if CloudProvider.AZURE in self.providers and not self.azure_client:
            raise ConfigurationError(
                "Azure client required but not configured",
                config_key="azure_client"
            )
        if CloudProvider.GCP in self.providers and not self.gcp_client:
            raise ConfigurationError(
                "GCP client required but not configured",
                config_key="gcp_client"
            )

    async def analyze_plan(
        self,
        plan_file: Union[str, Path],
        include_previous_costs: bool = False,
        currency: Optional[str] = None,
    ) -> CostAnalysis:
        """Analyze a Terraform plan file.

        Args:
            plan_file: Path to the plan file (JSON format).
            include_previous_costs: Whether to include previous costs.
            currency: Target currency for cost estimates.

        Returns:
            Cost analysis results.

        Raises:
            ValidationError: If input validation fails.
            PricingCalculationError: If cost calculation fails.
        """
        # Parse plan
        plan_data = self.parser.parse_plan_file(plan_file)

        # Extract resources and modules
        resources = self.parser.extract_resources(plan_data)
        modules = self.parser.extract_modules(plan_data)
        providers = self.parser.extract_providers(plan_data)
        regions = self.parser.extract_regions(plan_data)

        # Validate providers
        unsupported = providers - self.providers
        if unsupported:
            raise ValidationError(
                f"Unsupported providers: {', '.join(p.value for p in unsupported)}"
            )

        # Get pricing data
        pricing_data = await self._get_pricing_data(
            providers=providers,
            regions=regions,
            currency=currency or self.default_currency
        )

        # Calculate resource costs
        resource_costs = []
        for metadata, action in resources:
            cost = await self._calculate_resource_cost(
                metadata=metadata,
                action=action,
                pricing_data=pricing_data,
                include_previous=include_previous_costs
            )
            resource_costs.append(cost)

        # Calculate module costs
        module_costs = []
        for module in modules:
            module_resources = [
                cost for cost in resource_costs
                if cost.metadata.name.startswith(f"{module}.")
            ]
            if module_resources:
                cost = self._calculate_module_cost(
                    name=module,
                    resources=module_resources,
                    currency=currency or self.default_currency
                )
                module_costs.append(cost)

        # Create summary
        summary = self._create_summary(
            resources=resource_costs,
            currency=currency or self.default_currency
        )

        # Create analysis
        return CostAnalysis(
            project_name=Path(plan_file).stem,
            timestamp=datetime.utcnow(),
            provider_region_pairs=[
                (provider, region)
                for provider in providers
                for region in regions[provider]
            ],
            modules=module_costs,
            resources=resource_costs,
            summary=summary,
            currency=currency or self.default_currency,
            metadata={
                "plan_file": str(plan_file),
                "include_previous_costs": str(include_previous_costs),
            }
        )

    async def _get_pricing_data(
        self,
        providers: Set[CloudProvider],
        regions: Dict[CloudProvider, Set[str]],
        currency: str
    ) -> Dict[Tuple[CloudProvider, str], List[PricingData]]:
        """Get pricing data for resources.

        Args:
            providers: Set of cloud providers.
            regions: Dictionary mapping providers to their regions.
            currency: Target currency for pricing.

        Returns:
            Dictionary mapping (provider, region) to pricing data.

        Raises:
            PricingDataNotFoundError: If pricing data not found.
        """
        pricing_data = {}
        
        for provider in providers:
            for region in regions[provider]:
                key = (provider, region)
                
                try:
                    if provider == CloudProvider.AWS:
                        data = await self.aws_client.get_pricing_data(
                            region=region,
                            currency=currency
                        )
                    elif provider == CloudProvider.AZURE:
                        data = await self.azure_client.get_pricing_data(
                            region=region,
                            currency=currency
                        )
                    elif provider == CloudProvider.GCP:
                        data = await self.gcp_client.get_pricing_data(
                            region=region,
                            currency=currency
                        )
                    else:
                        continue

                    pricing_data[key] = data

                except Exception as e:
                    raise PricingDataNotFoundError(
                        f"Failed to get pricing data: {str(e)}",
                        provider=provider.value,
                        region=region
                    ) from e

        return pricing_data

    async def _calculate_resource_cost(
        self,
        metadata: ResourceMetadata,
        action: ResourceAction,
        pricing_data: Dict[Tuple[CloudProvider, str], List[PricingData]],
        include_previous: bool = False
    ) -> ResourceCost:
        """Calculate cost for a resource.

        Args:
            metadata: Resource metadata.
            action: Resource action.
            pricing_data: Dictionary of pricing data.
            include_previous: Whether to include previous costs.

        Returns:
            Resource cost estimate.

        Raises:
            PricingCalculationError: If cost calculation fails.
        """
        try:
            # Get pricing data for resource
            key = (metadata.provider, metadata.region)
            if key not in pricing_data:
                raise PricingCalculationError(
                    "Pricing data not found",
                    resource_type=metadata.type,
                    details={"provider": metadata.provider, "region": metadata.region}
                )

            # Find matching price
            price_data = None
            for data in pricing_data[key]:
                if (
                    data.resource_type == metadata.type
                    and data.pricing_tier == metadata.pricing_tier
                ):
                    price_data = data
                    break

            if not price_data:
                raise PricingCalculationError(
                    "No matching price found",
                    resource_type=metadata.type,
                    pricing_tier=metadata.pricing_tier.value
                )

            # Calculate costs
            components = []
            hourly_cost = Decimal("0")
            monthly_cost = Decimal("0")

            # Add base cost
            components.append(
                CostComponent(
                    name="Base Cost",
                    unit=price_data.unit,
                    hourly_cost=price_data.unit_price,
                    monthly_cost=price_data.unit_price * Decimal("730"),  # ~hours/month
                    details={"pricing_tier": price_data.pricing_tier.value}
                )
            )
            hourly_cost += price_data.unit_price
            monthly_cost += price_data.unit_price * Decimal("730")

            # Add storage cost if applicable
            if metadata.normalized_type in [ResourceType.STORAGE, ResourceType.DATABASE]:
                storage_price = await self._get_storage_price(
                    metadata=metadata,
                    pricing_data=pricing_data
                )
                if storage_price:
                    components.append(
                        CostComponent(
                            name="Storage",
                            unit="GB-month",
                            hourly_cost=storage_price / Decimal("730"),
                            monthly_cost=storage_price,
                            details={"type": "storage"}
                        )
                    )
                    hourly_cost += storage_price / Decimal("730")
                    monthly_cost += storage_price

            # Create resource cost
            return ResourceCost(
                id=f"{metadata.provider.value}-{metadata.name}",
                metadata=metadata,
                action=action,
                components=components,
                hourly_cost=hourly_cost,
                monthly_cost=monthly_cost,
                currency=price_data.currency,
                previous_cost=None,  # TODO: Implement previous cost lookup
                cost_change=None,
                usage_estimates={}  # TODO: Implement usage estimation
            )

        except Exception as e:
            raise PricingCalculationError(
                f"Failed to calculate resource cost: {str(e)}",
                resource_type=metadata.type,
                details={"original_error": str(e)}
            ) from e

    async def _get_storage_price(
        self,
        metadata: ResourceMetadata,
        pricing_data: Dict[Tuple[CloudProvider, str], List[PricingData]]
    ) -> Optional[Decimal]:
        """Get storage price for a resource.

        Args:
            metadata: Resource metadata.
            pricing_data: Dictionary of pricing data.

        Returns:
            Storage price per GB-month, or None if not applicable.
        """
        # TODO: Implement storage pricing logic
        return None

    def _calculate_module_cost(
        self,
        name: str,
        resources: List[ResourceCost],
        currency: str
    ) -> ModuleCost:
        """Calculate cost for a module.

        Args:
            name: Module name.
            resources: List of resource costs.
            currency: Target currency.

        Returns:
            Module cost estimate.
        """
        hourly_cost = sum(r.hourly_cost for r in resources)
        monthly_cost = sum(r.monthly_cost for r in resources)
        previous_cost = (
            sum(r.previous_cost for r in resources if r.previous_cost is not None)
            if any(r.previous_cost is not None for r in resources)
            else None
        )
        cost_change = (
            monthly_cost - previous_cost if previous_cost is not None else None
        )

        return ModuleCost(
            name=name,
            resources=resources,
            hourly_cost=hourly_cost,
            monthly_cost=monthly_cost,
            currency=currency,
            previous_cost=previous_cost,
            cost_change=cost_change
        )

    def _create_summary(
        self,
        resources: List[ResourceCost],
        currency: str
    ) -> CostSummary:
        """Create cost summary.

        Args:
            resources: List of resource costs.
            currency: Target currency.

        Returns:
            Cost summary.
        """
        # Count resources by action
        total = len(resources)
        to_add = sum(1 for r in resources if r.action == ResourceAction.CREATE)
        to_update = sum(1 for r in resources if r.action == ResourceAction.UPDATE)
        to_delete = sum(1 for r in resources if r.action == ResourceAction.DELETE)

        # Calculate total costs
        hourly_cost = sum(r.hourly_cost for r in resources)
        monthly_cost = sum(r.monthly_cost for r in resources)
        previous_cost = (
            sum(r.previous_cost for r in resources if r.previous_cost is not None)
            if any(r.previous_cost is not None for r in resources)
            else None
        )
        cost_change = (
            monthly_cost - previous_cost if previous_cost is not None else None
        )

        # Create cost breakdown
        breakdown = CostBreakdown()
        for resource in resources:
            if resource.action != ResourceAction.DELETE:
                field = resource.metadata.normalized_type.value
                current = getattr(breakdown, field)
                setattr(breakdown, field, current + resource.monthly_cost)

        return CostSummary(
            total_resources=total,
            resources_to_add=to_add,
            resources_to_update=to_update,
            resources_to_delete=to_delete,
            total_hourly_cost=hourly_cost,
            total_monthly_cost=monthly_cost,
            previous_total_monthly_cost=previous_cost,
            total_monthly_cost_change=cost_change,
            breakdown=breakdown,
            currency=currency
        )

    async def compare_regions(
        self,
        plan_file: Union[str, Path],
        target_regions: List[str],
        currency: Optional[str] = None,
    ) -> Dict[str, CostSummary]:
        """Compare costs across different regions.

        Args:
            plan_file: Path to the plan file.
            target_regions: List of regions to compare.
            currency: Target currency for cost estimates.

        Returns:
            Dictionary mapping regions to cost summaries.

        Raises:
            ValidationError: If input validation fails.
        """
        # TODO: Implement region comparison logic
        raise NotImplementedError("Region comparison not yet implemented")
