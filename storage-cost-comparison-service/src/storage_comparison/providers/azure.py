"""Azure storage provider implementation.

This module provides functionality for retrieving Azure storage information
and pricing data for Blob Storage, Managed Disks, and Files.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set

from azure.identity import ClientSecretCredential
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.commerce import UsageManagementClient
from azure.core.exceptions import AzureError

from storage_comparison.exceptions import (
    CapacityError,
    FeatureNotSupportedError,
    PerformanceTierNotSupportedError,
    PricingError,
    ProviderError,
    ReplicationNotSupportedError,
    StorageClassNotSupportedError,
)
from storage_comparison.models import (
    CloudProvider,
    CostComponent,
    OperationalMetrics,
    PricingTier,
    ReplicationType,
    StorageClass,
    StorageOption,
    StorageType,
)


logger = logging.getLogger(__name__)


class AzureStorageProvider:
    """Provider for Azure storage information and pricing."""

    # Maps our storage classes to Azure storage class values
    STORAGE_CLASS_MAPPING = {
        # Blob storage tiers
        StorageClass.STANDARD: "Hot",
        StorageClass.INFREQUENT: "Cool",
        StorageClass.ARCHIVE: "Archive",
        StorageClass.INTELLIGENT: "Premium",

        # Managed disk types
        StorageClass.PREMIUM: "Premium_LRS",
        StorageClass.PROVISIONED: "UltraSSD_LRS",

        # File storage tiers
        StorageClass.ONE_ZONE: "TransactionOptimized",
    }

    # Maps our replication types to Azure replication configurations
    REPLICATION_MAPPING = {
        ReplicationType.NONE: None,
        ReplicationType.LRS: "LRS",  # Locally redundant storage
        ReplicationType.ZRS: "ZRS",  # Zone-redundant storage
        ReplicationType.GRS: "GRS",  # Geo-redundant storage
        ReplicationType.RA_GRS: "RA-GRS",  # Read-access geo-redundant storage
    }

    # Features by storage class
    STORAGE_FEATURES = {
        # Blob storage features
        "Hot": {
            "versioning", "encryption", "immutable", "lifecycle",
            "static-website", "cdn-integration", "object-replication"
        },
        "Cool": {
            "versioning", "encryption", "immutable", "lifecycle",
            "object-replication"
        },
        "Archive": {
            "encryption", "immutable", "lifecycle"
        },
        "Premium": {
            "versioning", "encryption", "immutable", "lifecycle",
            "static-website", "cdn-integration", "object-replication",
            "high-performance"
        },

        # Managed disk features
        "Standard_LRS": {
            "encryption", "snapshots", "incremental-snapshots",
            "shared-disks"
        },
        "Premium_LRS": {
            "encryption", "snapshots", "incremental-snapshots",
            "shared-disks", "high-performance"
        },
        "UltraSSD_LRS": {
            "encryption", "snapshots", "incremental-snapshots",
            "shared-disks", "ultra-performance", "custom-iops",
            "custom-throughput"
        },

        # File storage features
        "TransactionOptimized": {
            "encryption", "snapshots", "backup", "active-directory",
            "identity-based-access"
        },
        "Premium_FileStorage": {
            "encryption", "snapshots", "backup", "active-directory",
            "identity-based-access", "high-performance"
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
        """Initialize Azure storage provider.

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
        self.storage_client = StorageManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )
        self.compute_client = ComputeManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )
        self.commerce_client = UsageManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )

    async def list_storage_options(
        self,
        storage_type: StorageType,
        region: Optional[str] = None,
    ) -> List[StorageOption]:
        """List available Azure storage options.

        Args:
            storage_type: Storage type (object, block, file)
            region: Optional region override

        Returns:
            List of storage options

        Raises:
            ProviderError: If error occurs getting storage options
        """
        try:
            region = region or self.location
            options = []

            if storage_type == StorageType.OBJECT:
                # Blob storage tiers
                options.extend([
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,  # No minimum
                        max_capacity_gb=None,  # No maximum
                        features=self.STORAGE_FEATURES["Hot"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.INFREQUENT,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["Cool"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.ARCHIVE,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["Archive"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.INTELLIGENT,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["Premium"],
                    ),
                ])

            elif storage_type == StorageType.BLOCK:
                # Managed disk types
                options.extend([
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=4,
                        max_capacity_gb=32767,  # 32 TiB
                        min_iops=500,
                        max_iops=2000,
                        min_throughput_mbps=60,
                        max_throughput_mbps=750,
                        features=self.STORAGE_FEATURES["Standard_LRS"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.PREMIUM,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=4,
                        max_capacity_gb=32767,
                        min_iops=120,
                        max_iops=160000,
                        min_throughput_mbps=25,
                        max_throughput_mbps=2000,
                        features=self.STORAGE_FEATURES["Premium_LRS"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.PROVISIONED,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=4,
                        max_capacity_gb=65536,  # 64 TiB
                        min_iops=100,
                        max_iops=160000,
                        min_throughput_mbps=1,
                        max_throughput_mbps=2000,
                        features=self.STORAGE_FEATURES["UltraSSD_LRS"],
                    ),
                ])

            elif storage_type == StorageType.FILE:
                # File storage tiers
                options.extend([
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.FILE,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=100,
                        max_capacity_gb=100 * 1024,  # 100 TiB
                        features=self.STORAGE_FEATURES["TransactionOptimized"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AZURE,
                        storage_type=StorageType.FILE,
                        storage_class=StorageClass.PREMIUM,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=100,
                        max_capacity_gb=100 * 1024,
                        features=self.STORAGE_FEATURES["Premium_FileStorage"],
                    ),
                ])

            return options

        except AzureError as e:
            raise ProviderError(
                f"Failed to list Azure storage options: {str(e)}",
                provider="azure",
                error_code=str(e),
            ) from e

    async def get_storage_costs(
        self,
        storage_type: StorageType,
        storage_class: StorageClass,
        replication_type: ReplicationType,
        region: str,
        capacity_gb: float,
    ) -> CostComponent:
        """Get storage costs.

        Args:
            storage_type: Storage type
            storage_class: Storage class
            replication_type: Replication type
            region: Region
            capacity_gb: Storage capacity in GB

        Returns:
            Storage cost component

        Raises:
            PricingError: If error occurs getting pricing
        """
        try:
            # Get rate card info
            azure_storage_class = self.STORAGE_CLASS_MAPPING[storage_class]
            azure_replication = self.REPLICATION_MAPPING[replication_type]

            rate_card = self.commerce_client.rate_card.get(
                filter=(
                    f"OfferDurableId eq 'MS-AZR-0003P' and "
                    f"Currency eq 'USD' and "
                    f"Locale eq 'en-US' and "
                    f"RegionInfo eq '{region}'"
                )
            )

            # Find matching meter
            meter = None
            for meter_info in rate_card.meters:
                if (
                    storage_type == StorageType.OBJECT
                    and meter_info.meter_category == "Storage"
                    and meter_info.meter_sub_category == "Block Blob"
                    and meter_info.meter_name.startswith(azure_storage_class)
                    and azure_replication in meter_info.meter_name
                ):
                    meter = meter_info
                    break
                elif (
                    storage_type == StorageType.BLOCK
                    and meter_info.meter_category == "Storage"
                    and meter_info.meter_sub_category == "Managed Disks"
                    and meter_info.meter_name.startswith(azure_storage_class)
                ):
                    meter = meter_info
                    break
                elif (
                    storage_type == StorageType.FILE
                    and meter_info.meter_category == "Storage"
                    and meter_info.meter_sub_category == "Files"
                    and meter_info.meter_name.startswith(azure_storage_class)
                    and azure_replication in meter_info.meter_name
                ):
                    meter = meter_info
                    break

            if not meter:
                raise PricingError(
                    f"No pricing found for storage type {storage_type.value}",
                    provider="azure",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Get monthly rate per GB
            gb_month_rate = Decimal(str(meter.meter_rates["0"]))
            monthly_cost = gb_month_rate * Decimal(str(capacity_gb))

            return CostComponent(
                name="Storage",
                monthly_cost=monthly_cost,
            )

        except AzureError as e:
            raise PricingError(
                f"Failed to get Azure storage pricing: {str(e)}",
                provider="azure",
                region=region,
                storage_type=storage_type.value,
                storage_class=storage_class.value,
            ) from e

    async def get_iops_costs(
        self,
        storage_type: StorageType,
        storage_class: StorageClass,
        region: str,
        iops: int,
    ) -> CostComponent:
        """Get IOPS costs for block storage.

        Args:
            storage_type: Storage type
            storage_class: Storage class
            region: Region
            iops: Requested IOPS

        Returns:
            IOPS cost component

        Raises:
            PricingError: If error occurs getting pricing
        """
        if storage_type != StorageType.BLOCK:
            return CostComponent(name="IOPS", monthly_cost=Decimal("0"))

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

            # Find IOPS meter
            meter = None
            azure_storage_class = self.STORAGE_CLASS_MAPPING[storage_class]
            for meter_info in rate_card.meters:
                if (
                    meter_info.meter_category == "Storage"
                    and meter_info.meter_sub_category == "Managed Disks"
                    and meter_info.meter_name.startswith(azure_storage_class)
                    and "IOPS" in meter_info.meter_name
                ):
                    meter = meter_info
                    break

            if not meter:
                raise PricingError(
                    "No IOPS pricing found",
                    provider="azure",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Get monthly rate per IOPS
            iops_month_rate = Decimal(str(meter.meter_rates["0"]))
            monthly_cost = iops_month_rate * Decimal(str(iops))

            return CostComponent(
                name="IOPS",
                monthly_cost=monthly_cost,
            )

        except AzureError as e:
            raise PricingError(
                f"Failed to get Azure IOPS pricing: {str(e)}",
                provider="azure",
                region=region,
                storage_type=storage_type.value,
                storage_class=storage_class.value,
            ) from e

    async def get_throughput_costs(
        self,
        storage_type: StorageType,
        storage_class: StorageClass,
        region: str,
        throughput_mbps: float,
    ) -> CostComponent:
        """Get throughput costs for block storage.

        Args:
            storage_type: Storage type
            storage_class: Storage class
            region: Region
            throughput_mbps: Requested throughput in MB/s

        Returns:
            Throughput cost component

        Raises:
            PricingError: If error occurs getting pricing
        """
        if storage_type != StorageType.BLOCK:
            return CostComponent(name="Throughput", monthly_cost=Decimal("0"))

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

            # Find throughput meter
            meter = None
            azure_storage_class = self.STORAGE_CLASS_MAPPING[storage_class]
            for meter_info in rate_card.meters:
                if (
                    meter_info.meter_category == "Storage"
                    and meter_info.meter_sub_category == "Managed Disks"
                    and meter_info.meter_name.startswith(azure_storage_class)
                    and "Throughput" in meter_info.meter_name
                ):
                    meter = meter_info
                    break

            if not meter:
                raise PricingError(
                    "No throughput pricing found",
                    provider="azure",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Get monthly rate per MB/s
            mbps_month_rate = Decimal(str(meter.meter_rates["0"]))
            monthly_cost = mbps_month_rate * Decimal(str(throughput_mbps))

            return CostComponent(
                name="Throughput",
                monthly_cost=monthly_cost,
            )

        except AzureError as e:
            raise PricingError(
                f"Failed to get Azure throughput pricing: {str(e)}",
                provider="azure",
                region=region,
                storage_type=storage_type.value,
                storage_class=storage_class.value,
            ) from e
