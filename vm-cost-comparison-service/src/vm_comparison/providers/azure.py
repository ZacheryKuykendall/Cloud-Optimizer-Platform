"""Azure VM provider implementation.

This module provides functionality for retrieving Azure VM instance information
and pricing data.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.commerce import UsageManagementClient
from azure.core.exceptions import AzureError

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


class AzureVmProvider:
    """Provider for Azure VM instance information and pricing."""

    # Maps our OS types to Azure platform values
    OS_MAPPING = {
        OperatingSystem.LINUX: "Linux",
        OperatingSystem.WINDOWS: "Windows",
        OperatingSystem.RHEL: "RHEL",
        OperatingSystem.SUSE: "SLES",
        OperatingSystem.UBUNTU: "Ubuntu",
    }

    # Maps our purchase options to Azure terms
    PURCHASE_OPTION_MAPPING = {
        PurchaseOption.ON_DEMAND: "Consumption",
        PurchaseOption.RESERVED_1_YEAR: "Reserved_1_Year",
        PurchaseOption.RESERVED_3_YEAR: "Reserved_3_Years",
        PurchaseOption.SPOT: "Spot",
    }

    # Instance features by series
    INSTANCE_FEATURES = {
        "Standard_B": {"burstable"},
        "Standard_D": {"balanced", "premium-storage"},
        "Standard_E": {"memory-optimized", "premium-storage"},
        "Standard_F": {"compute-optimized", "premium-storage"},
        "Standard_H": {"high-performance", "rdma"},
        "Standard_L": {"storage-optimized", "local-ssd"},
        "Standard_M": {"memory-optimized", "premium-storage"},
        "Standard_N": {"gpu", "nvidia"},
    }

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        subscription_id: str,
        location: str,
    ):
        """Initialize Azure VM provider.

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
        self.compute_client = ComputeManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )
        self.commerce_client = UsageManagementClient(
            credential=self.credentials,
            subscription_id=subscription_id,
        )

    async def list_instance_types(
        self,
        region: Optional[str] = None,
    ) -> List[VmInstanceType]:
        """List available Azure VM instance types.

        Args:
            region: Optional region override

        Returns:
            List of instance types

        Raises:
            ProviderError: If error occurs getting instance types
        """
        try:
            region = region or self.location
            instances = []

            # Get VM sizes for location
            sizes = self.compute_client.virtual_machine_sizes.list(
                location=region
            )

            for size in sizes:
                # Get series features
                series = size.name.split("_")[0] + "_" + size.name.split("_")[1]
                features = self.INSTANCE_FEATURES.get(series, set())

                # Add capabilities as features
                if size.premium_io:
                    features.add("premium-storage")
                if size.memory_in_mb >= size.number_of_cores * 7 * 1024:  # >7GB per core
                    features.add("memory-optimized")
                if size.number_of_cores >= size.memory_in_mb / 1024 / 2:  # >2 cores per GB
                    features.add("compute-optimized")
                if getattr(size, "gpu_number", 0) > 0:
                    features.add("gpu")

                # Create instance type
                instances.append(
                    VmInstanceType(
                        provider=CloudProvider.AZURE,
                        instance_type=size.name,
                        vcpus=size.number_of_cores,
                        memory_gb=size.memory_in_mb / 1024,
                        gpu_count=getattr(size, "gpu_number", 0),
                        gpu_type=getattr(size, "gpu_name", None),
                        local_disk_gb=size.resource_disk_size_in_mb / 1024,
                        network_bandwidth_gbps=None,  # Not exposed by API
                        features=features,
                    )
                )

            return instances

        except AzureError as e:
            raise ProviderError(
                f"Failed to list Azure instance types: {str(e)}",
                provider="azure",
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
            # Get rate card info
            platform = self.OS_MAPPING[operating_system]
            term = self.PURCHASE_OPTION_MAPPING[purchase_option]

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
                    meter_info.meter_category == "Virtual Machines"
                    and meter_info.meter_sub_category == platform
                    and meter_info.meter_name.startswith(instance_type)
                ):
                    meter = meter_info
                    break

            if not meter:
                raise PricingError(
                    f"No pricing found for instance type {instance_type}",
                    provider="azure",
                    region=region,
                    instance_type=instance_type,
                )

            # Get hourly rate
            hourly_rate = Decimal(str(meter.meter_rates["0"]))

            return CostComponent(
                name="Compute",
                hourly_cost=hourly_rate,
                monthly_cost=hourly_rate * 730,  # Average hours per month
            )

        except AzureError as e:
            raise PricingError(
                f"Failed to get Azure pricing: {str(e)}",
                provider="azure",
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
            # Get rate card info
            rate_card = self.commerce_client.rate_card.get(
                filter=(
                    f"OfferDurableId eq 'MS-AZR-0003P' and "
                    f"Currency eq 'USD' and "
                    f"Locale eq 'en-US' and "
                    f"RegionInfo eq '{region}'"
                )
            )

            # Find Premium SSD meter
            meter = None
            for meter_info in rate_card.meters:
                if (
                    meter_info.meter_category == "Storage"
                    and meter_info.meter_sub_category == "Premium SSD Managed Disks"
                    and meter_info.unit == "1/Month"
                ):
                    meter = meter_info
                    break

            if not meter:
                raise PricingError(
                    "No storage pricing found",
                    provider="azure",
                    region=region,
                    instance_type=instance_type,
                )

            # Get monthly rate per GB
            gb_month_rate = Decimal(str(meter.meter_rates["0"]))
            monthly_cost = gb_month_rate * Decimal(str(storage_gb))
            hourly_cost = monthly_cost / 730  # Average hours per month

            return CostComponent(
                name="Storage",
                hourly_cost=hourly_cost,
                monthly_cost=monthly_cost,
            )

        except AzureError as e:
            raise PricingError(
                f"Failed to get Azure storage pricing: {str(e)}",
                provider="azure",
                region=region,
                instance_type=instance_type,
            ) from e
