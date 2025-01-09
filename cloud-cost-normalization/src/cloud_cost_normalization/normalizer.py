"""Cloud cost normalization service.

This module provides the core functionality for normalizing cloud costs
across different providers into a standardized format.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Type, Union

from aws_cost_explorer import AWSCostExplorerClient
from azure_cost_management import AzureCostManagementClient
from gcp_billing import GCPBillingClient

from cloud_cost_normalization.currency import CurrencyService
from cloud_cost_normalization.exceptions import (
    DataNormalizationError,
    ProviderAPIError,
    ResourceMappingError,
    UnsupportedProviderError,
)
from cloud_cost_normalization.models import (
    BillingType,
    CloudProvider,
    CostAllocation,
    CostAggregation,
    CostBreakdown,
    NormalizedCostEntry,
    ResourceMapping,
    ResourceMetadata,
    ResourceType,
    UsageData,
)

logger = logging.getLogger(__name__)


class CloudCostNormalizer:
    """Service for normalizing cloud costs across providers."""

    def __init__(
        self,
        aws_client: Optional[AWSCostExplorerClient] = None,
        azure_client: Optional[AzureCostManagementClient] = None,
        gcp_client: Optional[GCPBillingClient] = None,
        currency_service: Optional[CurrencyService] = None,
        target_currency: str = "USD",
    ):
        """Initialize the normalizer.

        Args:
            aws_client: Optional AWS Cost Explorer client.
            azure_client: Optional Azure Cost Management client.
            gcp_client: Optional GCP Billing client.
            currency_service: Optional currency service for conversions.
            target_currency: Target currency for normalized costs.
        """
        self.aws_client = aws_client
        self.azure_client = azure_client
        self.gcp_client = gcp_client
        self.currency_service = currency_service or CurrencyService(
            base_currency=target_currency
        )
        self.target_currency = target_currency.upper()
        self._resource_mappings: Dict[CloudProvider, List[ResourceMapping]] = {}
        self._load_resource_mappings()

    def _load_resource_mappings(self) -> None:
        """Load resource type mappings for each provider."""
        # AWS mappings
        self._resource_mappings[CloudProvider.AWS] = [
            ResourceMapping(
                provider=CloudProvider.AWS,
                provider_type="Amazon Elastic Compute Cloud",
                normalized_type=ResourceType.COMPUTE,
                metadata_mapping={
                    "instanceType": "specifications.instance_type",
                    "region": "region",
                    "operatingSystem": "specifications.os",
                },
            ),
            ResourceMapping(
                provider=CloudProvider.AWS,
                provider_type="Amazon Simple Storage Service",
                normalized_type=ResourceType.STORAGE,
                metadata_mapping={
                    "storageClass": "specifications.storage_class",
                    "region": "region",
                },
            ),
            # Add more AWS mappings...
        ]

        # Azure mappings
        self._resource_mappings[CloudProvider.AZURE] = [
            ResourceMapping(
                provider=CloudProvider.AZURE,
                provider_type="Microsoft.Compute",
                normalized_type=ResourceType.COMPUTE,
                metadata_mapping={
                    "size": "specifications.instance_type",
                    "location": "region",
                    "os": "specifications.os",
                },
            ),
            ResourceMapping(
                provider=CloudProvider.AZURE,
                provider_type="Microsoft.Storage",
                normalized_type=ResourceType.STORAGE,
                metadata_mapping={
                    "tier": "specifications.storage_class",
                    "location": "region",
                },
            ),
            # Add more Azure mappings...
        ]

        # GCP mappings
        self._resource_mappings[CloudProvider.GCP] = [
            ResourceMapping(
                provider=CloudProvider.GCP,
                provider_type="Compute Engine",
                normalized_type=ResourceType.COMPUTE,
                metadata_mapping={
                    "machine_type": "specifications.instance_type",
                    "location": "region",
                    "os": "specifications.os",
                },
            ),
            ResourceMapping(
                provider=CloudProvider.GCP,
                provider_type="Cloud Storage",
                normalized_type=ResourceType.STORAGE,
                metadata_mapping={
                    "storage_class": "specifications.storage_class",
                    "location": "region",
                },
            ),
            # Add more GCP mappings...
        ]

    def _get_resource_mapping(
        self, provider: CloudProvider, provider_type: str
    ) -> ResourceMapping:
        """Get resource mapping for a provider-specific resource type.

        Args:
            provider: Cloud provider.
            provider_type: Provider-specific resource type.

        Returns:
            ResourceMapping for the provider type.

        Raises:
            ResourceMappingError: If no mapping exists for the provider type.
        """
        mappings = self._resource_mappings.get(provider, [])
        for mapping in mappings:
            if mapping.provider_type == provider_type:
                return mapping

        available = [m.provider_type for m in mappings]
        raise ResourceMappingError(
            f"No mapping found for {provider} resource type: {provider_type}",
            provider=provider.value,
            provider_type=provider_type,
            available_mappings=available,
        )

    def _normalize_aws_cost(
        self,
        cost_data: dict,
        start_time: datetime,
        end_time: datetime
    ) -> List[NormalizedCostEntry]:
        """Normalize AWS cost data.

        Args:
            cost_data: Raw AWS cost data.
            start_time: Start time of the cost period.
            end_time: End time of the cost period.

        Returns:
            List of normalized cost entries.

        Raises:
            DataNormalizationError: If normalization fails.
        """
        try:
            normalized_entries = []
            for item in cost_data["ResultsByTime"]:
                for group in item.get("Groups", []):
                    metrics = group.get("Metrics", {})
                    resource_id = group.get("Keys", [""])[0]

                    # Get resource details
                    resource_type = metrics.get("ResourceType", "")
                    mapping = self._get_resource_mapping(
                        CloudProvider.AWS, resource_type
                    )

                    # Create resource metadata
                    metadata = ResourceMetadata(
                        provider=CloudProvider.AWS,
                        provider_id=resource_id,
                        name=metrics.get("ResourceName", resource_id),
                        type=mapping.normalized_type,
                        region=metrics.get("Region", "unknown"),
                        billing_type=BillingType.ON_DEMAND,  # Default
                        specifications={},
                    )

                    # Map provider-specific metadata
                    for src, dest in mapping.metadata_mapping.items():
                        if src in metrics:
                            parts = dest.split(".")
                            target = metadata.specifications
                            for part in parts[:-1]:
                                target = target.setdefault(part, {})
                            target[parts[-1]] = metrics[src]

                    # Create cost breakdown
                    cost = Decimal(str(metrics.get("UnblendedCost", 0)))
                    breakdown = CostBreakdown(
                        compute=cost if mapping.normalized_type == ResourceType.COMPUTE else Decimal("0"),
                        storage=cost if mapping.normalized_type == ResourceType.STORAGE else Decimal("0"),
                        network=cost if mapping.normalized_type == ResourceType.NETWORK else Decimal("0"),
                        other=cost if mapping.normalized_type not in [
                            ResourceType.COMPUTE,
                            ResourceType.STORAGE,
                            ResourceType.NETWORK,
                        ] else Decimal("0"),
                    )

                    # Create normalized entry
                    entry = NormalizedCostEntry(
                        id=f"aws-{resource_id}-{start_time.isoformat()}",
                        account_id=cost_data.get("AccountId", "unknown"),
                        resource=metadata,
                        allocation=CostAllocation(
                            project=metrics.get("Project"),
                            cost_center=metrics.get("CostCenter"),
                            custom_tags=metrics.get("Tags", {}),
                        ),
                        cost_breakdown=breakdown,
                        currency=cost_data.get("Currency", "USD"),
                        start_time=start_time,
                        end_time=end_time,
                    )

                    normalized_entries.append(entry)

            return normalized_entries

        except Exception as e:
            raise DataNormalizationError(
                f"Failed to normalize AWS cost data: {str(e)}",
                provider="aws",
                details={"original_error": str(e)},
            )

    def _normalize_azure_cost(
        self,
        cost_data: dict,
        start_time: datetime,
        end_time: datetime
    ) -> List[NormalizedCostEntry]:
        """Normalize Azure cost data.

        Args:
            cost_data: Raw Azure cost data.
            start_time: Start time of the cost period.
            end_time: End time of the cost period.

        Returns:
            List of normalized cost entries.

        Raises:
            DataNormalizationError: If normalization fails.
        """
        try:
            normalized_entries = []
            for item in cost_data.get("properties", {}).get("rows", []):
                resource_id = item.get("resourceId", "")
                resource_type = item.get("resourceType", "")
                mapping = self._get_resource_mapping(
                    CloudProvider.AZURE, resource_type
                )

                # Create resource metadata
                metadata = ResourceMetadata(
                    provider=CloudProvider.AZURE,
                    provider_id=resource_id,
                    name=item.get("resourceName", resource_id),
                    type=mapping.normalized_type,
                    region=item.get("location", "unknown"),
                    billing_type=BillingType.ON_DEMAND,  # Default
                    specifications={},
                )

                # Map provider-specific metadata
                for src, dest in mapping.metadata_mapping.items():
                    if src in item:
                        parts = dest.split(".")
                        target = metadata.specifications
                        for part in parts[:-1]:
                            target = target.setdefault(part, {})
                        target[parts[-1]] = item[src]

                # Create cost breakdown
                cost = Decimal(str(item.get("cost", 0)))
                breakdown = CostBreakdown(
                    compute=cost if mapping.normalized_type == ResourceType.COMPUTE else Decimal("0"),
                    storage=cost if mapping.normalized_type == ResourceType.STORAGE else Decimal("0"),
                    network=cost if mapping.normalized_type == ResourceType.NETWORK else Decimal("0"),
                    other=cost if mapping.normalized_type not in [
                        ResourceType.COMPUTE,
                        ResourceType.STORAGE,
                        ResourceType.NETWORK,
                    ] else Decimal("0"),
                )

                # Create normalized entry
                entry = NormalizedCostEntry(
                    id=f"azure-{resource_id}-{start_time.isoformat()}",
                    account_id=item.get("subscriptionId", "unknown"),
                    resource=metadata,
                    allocation=CostAllocation(
                        project=item.get("project"),
                        cost_center=item.get("costCenter"),
                        custom_tags=item.get("tags", {}),
                    ),
                    cost_breakdown=breakdown,
                    currency=item.get("currency", "USD"),
                    start_time=start_time,
                    end_time=end_time,
                )

                normalized_entries.append(entry)

            return normalized_entries

        except Exception as e:
            raise DataNormalizationError(
                f"Failed to normalize Azure cost data: {str(e)}",
                provider="azure",
                details={"original_error": str(e)},
            )

    def _normalize_gcp_cost(
        self,
        cost_data: dict,
        start_time: datetime,
        end_time: datetime
    ) -> List[NormalizedCostEntry]:
        """Normalize GCP cost data.

        Args:
            cost_data: Raw GCP cost data.
            start_time: Start time of the cost period.
            end_time: End time of the cost period.

        Returns:
            List of normalized cost entries.

        Raises:
            DataNormalizationError: If normalization fails.
        """
        try:
            normalized_entries = []
            for item in cost_data.get("billing_data", []):
                resource_id = item.get("resource", {}).get("id", "")
                resource_type = item.get("service", {}).get("description", "")
                mapping = self._get_resource_mapping(
                    CloudProvider.GCP, resource_type
                )

                # Create resource metadata
                metadata = ResourceMetadata(
                    provider=CloudProvider.GCP,
                    provider_id=resource_id,
                    name=item.get("resource", {}).get("name", resource_id),
                    type=mapping.normalized_type,
                    region=item.get("location", {}).get("region", "unknown"),
                    billing_type=BillingType.ON_DEMAND,  # Default
                    specifications={},
                )

                # Map provider-specific metadata
                for src, dest in mapping.metadata_mapping.items():
                    if src in item:
                        parts = dest.split(".")
                        target = metadata.specifications
                        for part in parts[:-1]:
                            target = target.setdefault(part, {})
                        target[parts[-1]] = item[src]

                # Create cost breakdown
                cost = Decimal(str(item.get("cost", {}).get("amount", 0)))
                breakdown = CostBreakdown(
                    compute=cost if mapping.normalized_type == ResourceType.COMPUTE else Decimal("0"),
                    storage=cost if mapping.normalized_type == ResourceType.STORAGE else Decimal("0"),
                    network=cost if mapping.normalized_type == ResourceType.NETWORK else Decimal("0"),
                    other=cost if mapping.normalized_type not in [
                        ResourceType.COMPUTE,
                        ResourceType.STORAGE,
                        ResourceType.NETWORK,
                    ] else Decimal("0"),
                )

                # Create normalized entry
                entry = NormalizedCostEntry(
                    id=f"gcp-{resource_id}-{start_time.isoformat()}",
                    account_id=item.get("billing_account_id", "unknown"),
                    resource=metadata,
                    allocation=CostAllocation(
                        project=item.get("project", {}).get("id"),
                        cost_center=item.get("labels", {}).get("cost_center"),
                        custom_tags=item.get("labels", {}),
                    ),
                    cost_breakdown=breakdown,
                    currency=item.get("cost", {}).get("currency", "USD"),
                    start_time=start_time,
                    end_time=end_time,
                )

                normalized_entries.append(entry)

            return normalized_entries

        except Exception as e:
            raise DataNormalizationError(
                f"Failed to normalize GCP cost data: {str(e)}",
                provider="gcp",
                details={"original_error": str(e)},
            )

    async def normalize_costs(
        self,
        provider: CloudProvider,
        start_time: datetime,
        end_time: datetime,
        **kwargs
    ) -> List[NormalizedCostEntry]:
        """Normalize cost data from a specific provider.

        Args:
            provider: Cloud provider to get costs from.
            start_time: Start time of the cost period.
            end_time: End time of the cost period.
            **kwargs: Additional provider-specific parameters.

        Returns:
            List of normalized cost entries.

        Raises:
            UnsupportedProviderError: If the provider is not supported.
            ProviderAPIError: If the provider API call fails.
            DataNormalizationError: If normalization fails.
        """
        try:
            # Get raw cost data from provider
            if provider == CloudProvider.AWS:
                if not self.aws_client:
                    raise UnsupportedProviderError(
                        "AWS client not configured",
                        provider="aws"
                    )
                raw_data = await self.aws_client.get_cost_and_usage(
                    start_time=start_time,
                    end_time=end_time,
                    **kwargs
                )
                entries = self._normalize_aws_cost(
                    raw_data,
                    start_time,
                    end_time
                )

            elif provider == CloudProvider.AZURE:
                if not self.azure_client:
                    raise UnsupportedProviderError(
                        "Azure client not configured",
                        provider="azure"
                    )
                raw_data = await self.azure_client.get_cost_details(
                    start_time=start_time,
                    end_time=end_time,
                    **kwargs
                )
                entries = self._normalize_azure_cost(
                    raw_data,
                    start_time,
                    end_time
                )

            elif provider == CloudProvider.GCP:
                if not self.gcp_client:
                    raise UnsupportedProviderError(
                        "GCP client not configured",
                        provider="gcp"
                    )
                raw_data = await self.gcp_client.get_billing_data(
                    start_time=start_time,
                    end_time=end_time,
                    **kwargs
                )
                entries = self._normalize_gcp_cost(
                    raw_data,
                    start_time,
                    end_time
                )

            else:
                raise UnsupportedProviderError(
                    f"Unsupported provider: {provider}",
                    provider=provider.value
                )

            # Convert all costs to target currency
            for entry in entries:
                if entry.currency != self.target_currency:
                    for field in entry.cost_breakdown.__fields__:
                        original = getattr(entry.cost_breakdown, field)
                        if original > 0:
                            converted = self.currency_service.convert_amount(
                                original,
                                entry.currency,
                                self.target_currency
                            )
                            setattr(entry.cost_breakdown, field, converted)
                    entry.currency = self.target_currency

            return entries

        except Exception as e:
            if isinstance(e, (UnsupportedProviderError, DataNormalizationError)):
                raise
            raise ProviderAPIError(
                f"Failed to get cost data from {provider}: {str(e)}",
                provider=provider.value,
                details={"original_error": str(e)},
            )

    async def aggregate_costs(
        self,
        entries: List[NormalizedCostEntry],
        group_by: List[str],
        time_period: str = "total"
    ) -> CostAggregation:
        """Aggregate normalized cost entries.

        Args:
            entries: List of normalized cost entries to aggregate.
            group_by: List of fields to group by (e.g., ["provider", "resource.type"]).
            time_period: Time period for aggregation ("total", "daily", "monthly").

        Returns:
            Aggregated cost data.

        Raises:
            AggregationError: If aggregation fails.
        """
        try:
            # Initialize aggregation
            costs: Dict[str, Decimal] = {}
            resource_counts: Dict[str, int] = {}
            total_cost = Decimal("0")
            start_time = min(entry.start_time for entry in entries)
            end_time = max(entry.end_time for entry in entries)

            # Group entries
            for entry in entries:
                # Build group key
                key_parts = []
                for field in group_by:
                    value = entry
                    for part in field.split("."):
                        value = getattr(value, part)
                    key_parts.append(str(value))
                group_key = ":".join(key_parts) if key_parts else "total"

                # Update aggregations
                costs[group_key] = costs.get(group_key, Decimal("0")) + entry.total_cost
                resource_counts[group_key] = resource_counts.get(group_key, 0) + 1
                total_cost += entry.total_cost

            return CostAggregation(
                group_by=group_by,
                time_period=time_period,
                costs=costs,
                resource_counts=resource_counts,
                total_cost=total_cost,
                currency=self.target_currency,
                start_time=start_time,
                end_time=end_time,
            )

        except Exception as e:
            raise AggregationError(
                f"Failed to aggregate costs: {str(e)}",
                group_by=group_by,
                time_period=time_period,
            )
