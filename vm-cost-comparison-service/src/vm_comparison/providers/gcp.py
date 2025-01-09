"""GCP VM provider implementation.

This module provides functionality for retrieving Google Cloud VM instance information
and pricing data.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from google.cloud import compute_v1
from google.cloud import billing_v1
from google.api_core import exceptions as google_exceptions

from vm_comparison.exceptions import (
    FeatureNotSupportedError,
    PricingError,
    ProviderError,
)
from vm_comparison.models import (
    CloudProvider,
    CostComponent,
    OperatingSystem,
    PurchaseOption,
    VmInstanceType,
)


logger = logging.getLogger(__name__)


class GcpVmProvider:
    """Provider for GCP VM instance information and pricing."""

    # Maps our OS types to GCP platform values
    OS_MAPPING = {
        OperatingSystem.LINUX: "linux",
        OperatingSystem.WINDOWS: "windows",
        OperatingSystem.RHEL: "rhel",
        OperatingSystem.SUSE: "sles",
        OperatingSystem.UBUNTU: "ubuntu",
    }

    # Maps our purchase options to GCP commitment types
    PURCHASE_OPTION_MAPPING = {
        PurchaseOption.ON_DEMAND: None,  # No commitment
        PurchaseOption.RESERVED_1_YEAR: "1-year",
        PurchaseOption.RESERVED_3_YEAR: "3-year",
        PurchaseOption.SPOT: "spot",
    }

    # Instance features by series
    INSTANCE_FEATURES = {
        "e2": {"cost-optimized"},
        "n2": {"balanced", "intel"},
        "n2d": {"balanced", "amd"},
        "c2": {"compute-optimized", "intel"},
        "m2": {"memory-optimized"},
        "a2": {"gpu", "nvidia-ampere"},
        "t2": {"gpu", "nvidia-tesla"},
    }

    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        credentials_dict: Optional[Dict] = None,
        region: str = "us-central1",
    ):
        """Initialize GCP VM provider.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file
            credentials_dict: Service account credentials as dictionary
            region: GCP region
        """
        self.project_id = project_id
        self.region = region

        # Initialize clients
        self.compute_client = compute_v1.InstancesClient()
        self.billing_client = billing_v1.CloudCatalogClient()

    async def list_instance_types(
        self,
        region: Optional[str] = None,
    ) -> List[VmInstanceType]:
        """List available GCP VM instance types.

        Args:
            region: Optional region override

        Returns:
            List of instance types

        Raises:
            ProviderError: If error occurs getting instance types
        """
        try:
            region = region or self.region
            instances = []
            zone = f"{region}-a"  # Use first zone in region

            # Get machine types for zone
            request = compute_v1.ListMachineTypesRequest(
                project=self.project_id,
                zone=zone,
            )
            machine_types = self.compute_client.list_machine_types(request=request)

            for machine_type in machine_types:
                # Get series features
                series = machine_type.name.split("-")[0]
                features = self.INSTANCE_FEATURES.get(series, set())

                # Add capabilities as features
                if machine_type.is_shared_cpu:
                    features.add("shared-cpu")
                if getattr(machine_type, "accelerators", None):
                    features.add("gpu")
                    for acc in machine_type.accelerators:
                        if "nvidia" in acc.guest_accelerator_type.lower():
                            features.add("nvidia")
                        if "tpu" in acc.guest_accelerator_type.lower():
                            features.add("tpu")

                # Create instance type
                instances.append(
                    VmInstanceType(
                        provider=CloudProvider.GCP,
                        instance_type=machine_type.name,
                        vcpus=machine_type.guest_cpus,
                        memory_gb=machine_type.memory_mb / 1024,
                        gpu_count=sum(
                            acc.guest_accelerator_count
                            for acc in getattr(machine_type, "accelerators", [])
                        ),
                        gpu_type=next(
                            (
                                acc.guest_accelerator_type
                                for acc in getattr(machine_type, "accelerators", [])
                                if "nvidia" in acc.guest_accelerator_type.lower()
                            ),
                            None,
                        ),
                        local_disk_gb=None,  # Local SSD is added separately
                        network_bandwidth_gbps=None,  # Not exposed by API
                        features=features,
                    )
                )

            return instances

        except google_exceptions.GoogleAPIError as e:
            raise ProviderError(
                f"Failed to list GCP instance types: {str(e)}",
                provider="gcp",
                error_code=str(e),
            ) from e

    async def get_compute_costs(
        self,
        instance_type: str,
        region: str,
        operating_system: OperatingSystem,
        purchase_option: PurchaseOption = PurchaseOption.ON_DEMAND,
    ) -> CostComponent:
        """Get compute costs for an instance type.

        Args:
            instance_type: Instance type
            region: Region
            operating_system: Operating system
            purchase_option: Purchase option

        Returns:
            Compute cost component

        Raises:
            PricingError: If error occurs getting pricing
        """
        try:
            # Get pricing info
            platform = self.OS_MAPPING[operating_system]
            commitment_type = self.PURCHASE_OPTION_MAPPING[purchase_option]

            # Build SKU filter
            filters = [
                f"serviceId:6F81-5844-456A",  # Compute Engine
                f"region:{region}",
                f"machineType:{instance_type}",
                f"operatingSystem:{platform}",
            ]
            if commitment_type:
                filters.append(f"commitmentType:{commitment_type}")

            request = billing_v1.ListSkusRequest(
                parent=f"services/6F81-5844-456A",  # Compute Engine
                filter=" AND ".join(filters),
            )

            # Get matching SKU
            skus = self.billing_client.list_skus(request=request)
            sku = next(skus, None)

            if not sku:
                raise PricingError(
                    f"No pricing found for instance type {instance_type}",
                    provider="gcp",
                    region=region,
                    instance_type=instance_type,
                )

            # Get hourly rate
            pricing_info = sku.pricing_info[0]
            price_expression = pricing_info.pricing_expression
            unit_price = price_expression.tiered_rates[0].unit_price

            hourly_rate = Decimal(str(unit_price.nanos / 1e9))
            if unit_price.units:
                hourly_rate += Decimal(str(unit_price.units))

            return CostComponent(
                name="Compute",
                hourly_cost=hourly_rate,
                monthly_cost=hourly_rate * 730,  # Average hours per month
            )

        except google_exceptions.GoogleAPIError as e:
            raise PricingError(
                f"Failed to get GCP pricing: {str(e)}",
                provider="gcp",
                region=region,
                instance_type=instance_type,
            ) from e

    async def get_storage_costs(
        self,
        instance_type: str,
        region: str,
        storage_gb: float,
    ) -> CostComponent:
        """Get storage costs for an instance type.

        Args:
            instance_type: Instance type
            region: Region
            storage_gb: Storage size in GB

        Returns:
            Storage cost component

        Raises:
            PricingError: If error occurs getting pricing
        """
        try:
            # Get persistent disk pricing
            request = billing_v1.ListSkusRequest(
                parent=f"services/6F81-5844-456A",  # Compute Engine
                filter=(
                    f"serviceId:6F81-5844-456A AND "  # Compute Engine
                    f"region:{region} AND "
                    f"description:SSD AND "
                    f"description:Persistent"
                ),
            )

            # Get matching SKU
            skus = self.billing_client.list_skus(request=request)
            sku = next(skus, None)

            if not sku:
                raise PricingError(
                    "No storage pricing found",
                    provider="gcp",
                    region=region,
                    instance_type=instance_type,
                )

            # Get monthly rate per GB
            pricing_info = sku.pricing_info[0]
            price_expression = pricing_info.pricing_expression
            unit_price = price_expression.tiered_rates[0].unit_price

            gb_month_rate = Decimal(str(unit_price.nanos / 1e9))
            if unit_price.units:
                gb_month_rate += Decimal(str(unit_price.units))

            monthly_cost = gb_month_rate * Decimal(str(storage_gb))
            hourly_cost = monthly_cost / 730  # Average hours per month

            return CostComponent(
                name="Storage",
                hourly_cost=hourly_cost,
                monthly_cost=monthly_cost,
            )

        except google_exceptions.GoogleAPIError as e:
            raise PricingError(
                f"Failed to get GCP storage pricing: {str(e)}",
                provider="gcp",
                region=region,
                instance_type=instance_type,
            ) from e
