"""GCP storage provider implementation.

This module provides functionality for retrieving Google Cloud storage information
and pricing data for Cloud Storage, Persistent Disk, and Filestore.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set

from google.cloud import storage_v1
from google.cloud import compute_v1
from google.cloud import billing_v1
from google.api_core import exceptions as google_exceptions

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


class GcpStorageProvider:
    """Provider for GCP storage information and pricing."""

    # Maps our storage classes to GCP storage class values
    STORAGE_CLASS_MAPPING = {
        # Cloud Storage classes
        StorageClass.STANDARD: "STANDARD",
        StorageClass.INFREQUENT: "NEARLINE",
        StorageClass.ARCHIVE: "COLDLINE",
        StorageClass.DEEP_ARCHIVE: "ARCHIVE",

        # Persistent Disk types
        StorageClass.PREMIUM: "pd-ssd",
        StorageClass.PROVISIONED: "hyperdisk-extreme",

        # Filestore tiers
        StorageClass.ONE_ZONE: "BASIC_HDD",
    }

    # Maps our replication types to GCP replication configurations
    REPLICATION_MAPPING = {
        ReplicationType.NONE: None,
        ReplicationType.LRS: "regional",  # Single region
        ReplicationType.ZRS: "multi-regional",  # Multiple zones in a region
        ReplicationType.GRS: "dual-region",  # Two regions
        ReplicationType.RA_GRS: "turbo-replication",  # Dual-region with faster replication
    }

    # Features by storage class
    STORAGE_FEATURES = {
        # Cloud Storage features
        "STANDARD": {
            "versioning", "encryption", "lifecycle", "retention",
            "object-hold", "cors", "cdn-integration", "customer-encryption"
        },
        "NEARLINE": {
            "versioning", "encryption", "lifecycle", "retention",
            "object-hold", "customer-encryption"
        },
        "COLDLINE": {
            "versioning", "encryption", "lifecycle", "retention",
            "object-hold", "customer-encryption"
        },
        "ARCHIVE": {
            "encryption", "lifecycle", "retention",
            "object-hold", "customer-encryption"
        },

        # Persistent Disk features
        "pd-standard": {
            "encryption", "snapshots", "multi-attach",
            "regional-pd", "performance-monitoring"
        },
        "pd-balanced": {
            "encryption", "snapshots", "multi-attach",
            "regional-pd", "performance-monitoring"
        },
        "pd-ssd": {
            "encryption", "snapshots", "multi-attach",
            "regional-pd", "performance-monitoring",
            "high-performance"
        },
        "hyperdisk-extreme": {
            "encryption", "snapshots", "multi-attach",
            "regional-pd", "performance-monitoring",
            "ultra-performance", "custom-iops",
            "custom-throughput"
        },

        # Filestore features
        "BASIC_HDD": {
            "encryption", "snapshots", "backup",
            "nfs-access", "smb-access"
        },
        "ENTERPRISE": {
            "encryption", "snapshots", "backup",
            "nfs-access", "smb-access",
            "high-performance", "ha-configuration"
        },
    }

    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        credentials_dict: Optional[Dict] = None,
        region: str = "us-central1",
    ):
        """Initialize GCP storage provider.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file
            credentials_dict: Service account credentials as dictionary
            region: GCP region
        """
        self.project_id = project_id
        self.region = region

        # Initialize clients
        self.storage_client = storage_v1.StorageClient()
        self.compute_client = compute_v1.DisksClient()
        self.billing_client = billing_v1.CloudCatalogClient()

    async def list_storage_options(
        self,
        storage_type: StorageType,
        region: Optional[str] = None,
    ) -> List[StorageOption]:
        """List available GCP storage options.

        Args:
            storage_type: Storage type (object, block, file)
            region: Optional region override

        Returns:
            List of storage options

        Raises:
            ProviderError: If error occurs getting storage options
        """
        try:
            region = region or self.region
            options = []

            if storage_type == StorageType.OBJECT:
                # Cloud Storage classes
                options.extend([
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,  # No minimum
                        max_capacity_gb=None,  # No maximum
                        features=self.STORAGE_FEATURES["STANDARD"],
                    ),
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.INFREQUENT,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["NEARLINE"],
                    ),
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.ARCHIVE,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["COLDLINE"],
                    ),
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.DEEP_ARCHIVE,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["ARCHIVE"],
                    ),
                ])

            elif storage_type == StorageType.BLOCK:
                # Persistent Disk types
                options.extend([
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=10,
                        max_capacity_gb=64 * 1024,  # 64 TiB
                        min_iops=3000,
                        max_iops=15000,
                        min_throughput_mbps=75,
                        max_throughput_mbps=240,
                        features=self.STORAGE_FEATURES["pd-standard"],
                    ),
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.PREMIUM,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=10,
                        max_capacity_gb=64 * 1024,
                        min_iops=6000,
                        max_iops=30000,
                        min_throughput_mbps=150,
                        max_throughput_mbps=480,
                        features=self.STORAGE_FEATURES["pd-ssd"],
                    ),
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.PROVISIONED,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=10,
                        max_capacity_gb=64 * 1024,
                        min_iops=10000,
                        max_iops=120000,
                        min_throughput_mbps=200,
                        max_throughput_mbps=1200,
                        features=self.STORAGE_FEATURES["hyperdisk-extreme"],
                    ),
                ])

            elif storage_type == StorageType.FILE:
                # Filestore instances
                options.extend([
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.FILE,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=1024,  # 1 TiB
                        max_capacity_gb=64 * 1024,  # 64 TiB
                        features=self.STORAGE_FEATURES["BASIC_HDD"],
                    ),
                    StorageOption(
                        provider=CloudProvider.GCP,
                        storage_type=StorageType.FILE,
                        storage_class=StorageClass.PREMIUM,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=1024,
                        max_capacity_gb=64 * 1024,
                        features=self.STORAGE_FEATURES["ENTERPRISE"],
                    ),
                ])

            return options

        except google_exceptions.GoogleAPIError as e:
            raise ProviderError(
                f"Failed to list GCP storage options: {str(e)}",
                provider="gcp",
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
            # Get pricing info
            gcp_storage_class = self.STORAGE_CLASS_MAPPING[storage_class]
            gcp_replication = self.REPLICATION_MAPPING[replication_type]

            # Build SKU filter
            filters = [
                f"serviceId:6F81-5844-456A",  # Cloud Storage
                f"region:{region}",
            ]

            if storage_type == StorageType.OBJECT:
                filters.extend([
                    f"resourceFamily:Storage",
                    f"resourceGroup:StorageObject",
                    f"storageClass:{gcp_storage_class}",
                ])
                if gcp_replication:
                    filters.append(f"replicationType:{gcp_replication}")

            elif storage_type == StorageType.BLOCK:
                filters.extend([
                    f"resourceFamily:Storage",
                    f"resourceGroup:PDDisk",
                    f"diskType:{gcp_storage_class}",
                ])

            else:  # FILE
                filters.extend([
                    f"resourceFamily:Storage",
                    f"resourceGroup:Filestore",
                    f"tier:{gcp_storage_class}",
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
                    f"No pricing found for storage type {storage_type.value}",
                    provider="gcp",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Get monthly rate per GB
            pricing_info = sku.pricing_info[0]
            price_expression = pricing_info.pricing_expression
            unit_price = price_expression.tiered_rates[0].unit_price

            gb_month_rate = Decimal(str(unit_price.nanos / 1e9))
            if unit_price.units:
                gb_month_rate += Decimal(str(unit_price.units))

            monthly_cost = gb_month_rate * Decimal(str(capacity_gb))

            return CostComponent(
                name="Storage",
                monthly_cost=monthly_cost,
            )

        except google_exceptions.GoogleAPIError as e:
            raise PricingError(
                f"Failed to get GCP storage pricing: {str(e)}",
                provider="gcp",
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
            # Get pricing info
            request = billing_v1.ListSkusRequest(
                parent=f"services/6F81-5844-456A",
                filter=(
                    f"serviceId:6F81-5844-456A AND "  # Cloud Storage
                    f"region:{region} AND "
                    f"resourceFamily:Storage AND "
                    f"resourceGroup:PDDisk AND "
                    f"description:IOPS AND "
                    f"diskType:{self.STORAGE_CLASS_MAPPING[storage_class]}"
                ),
            )

            # Get matching SKU
            skus = self.billing_client.list_skus(request=request)
            sku = next(skus, None)

            if not sku:
                raise PricingError(
                    "No IOPS pricing found",
                    provider="gcp",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Get monthly rate per IOPS
            pricing_info = sku.pricing_info[0]
            price_expression = pricing_info.pricing_expression
            unit_price = price_expression.tiered_rates[0].unit_price

            iops_month_rate = Decimal(str(unit_price.nanos / 1e9))
            if unit_price.units:
                iops_month_rate += Decimal(str(unit_price.units))

            monthly_cost = iops_month_rate * Decimal(str(iops))

            return CostComponent(
                name="IOPS",
                monthly_cost=monthly_cost,
            )

        except google_exceptions.GoogleAPIError as e:
            raise PricingError(
                f"Failed to get GCP IOPS pricing: {str(e)}",
                provider="gcp",
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
            # Get pricing info
            request = billing_v1.ListSkusRequest(
                parent=f"services/6F81-5844-456A",
                filter=(
                    f"serviceId:6F81-5844-456A AND "  # Cloud Storage
                    f"region:{region} AND "
                    f"resourceFamily:Storage AND "
                    f"resourceGroup:PDDisk AND "
                    f"description:Throughput AND "
                    f"diskType:{self.STORAGE_CLASS_MAPPING[storage_class]}"
                ),
            )

            # Get matching SKU
            skus = self.billing_client.list_skus(request=request)
            sku = next(skus, None)

            if not sku:
                raise PricingError(
                    "No throughput pricing found",
                    provider="gcp",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Get monthly rate per MB/s
            pricing_info = sku.pricing_info[0]
            price_expression = pricing_info.pricing_expression
            unit_price = price_expression.tiered_rates[0].unit_price

            mbps_month_rate = Decimal(str(unit_price.nanos / 1e9))
            if unit_price.units:
                mbps_month_rate += Decimal(str(unit_price.units))

            monthly_cost = mbps_month_rate * Decimal(str(throughput_mbps))

            return CostComponent(
                name="Throughput",
                monthly_cost=monthly_cost,
            )

        except google_exceptions.GoogleAPIError as e:
            raise PricingError(
                f"Failed to get GCP throughput pricing: {str(e)}",
                provider="gcp",
                region=region,
                storage_type=storage_type.value,
                storage_class=storage_class.value,
            ) from e
