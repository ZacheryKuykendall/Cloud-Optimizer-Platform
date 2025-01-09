"""AWS VM provider implementation.

This module provides functionality for retrieving AWS EC2 instance information
and pricing data.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

import boto3
from botocore.exceptions import BotoCoreError, ClientError

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


class AwsVmProvider:
    """Provider for AWS VM instance information and pricing."""

    # Maps our OS types to AWS platform values
    OS_MAPPING = {
        OperatingSystem.LINUX: "Linux",
        OperatingSystem.WINDOWS: "Windows",
        OperatingSystem.RHEL: "RHEL",
        OperatingSystem.SUSE: "SUSE",
        OperatingSystem.UBUNTU: "Ubuntu",
    }

    # Maps our purchase options to AWS offering class/terms
    PURCHASE_OPTION_MAPPING = {
        PurchaseOption.ON_DEMAND: ("OnDemand", "OnDemand"),
        PurchaseOption.RESERVED_1_YEAR: ("Reserved", "Reserved"),
        PurchaseOption.RESERVED_3_YEAR: ("Reserved", "Reserved"),
        PurchaseOption.SPOT: ("Spot", "Spot"),
    }

    # Instance features by family
    INSTANCE_FEATURES = {
        "t3": {"burstable", "ebs-only"},
        "m5": {"ebs-optimized", "nvme"},
        "c5": {"ebs-optimized", "nvme", "cpu-optimized"},
        "r5": {"ebs-optimized", "nvme", "memory-optimized"},
        "p3": {"gpu", "nvidia", "ebs-optimized"},
        "g4": {"gpu", "nvidia", "nvme", "ebs-optimized"},
    }

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str,
    ):
        """Initialize AWS VM provider.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region
        """
        self.region = region
        
        # Initialize clients
        self.ec2_client = boto3.client(
            "ec2",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )
        self.pricing_client = boto3.client(
            "pricing",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name="us-east-1",  # Pricing API only available in us-east-1
        )

    async def list_instance_types(
        self,
        region: Optional[str] = None,
    ) -> List[VmInstanceType]:
        """List available EC2 instance types.

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

            # Get instance type offerings for region
            paginator = self.ec2_client.get_paginator("describe_instance_types")
            async for page in paginator.paginate():
                for instance in page["InstanceTypes"]:
                    # Get instance family features
                    family = instance["InstanceType"].split(".")[0]
                    features = self.INSTANCE_FEATURES.get(family, set())

                    # Add instance capabilities as features
                    if instance.get("EbsInfo", {}).get("EbsOptimizedSupport") == "supported":
                        features.add("ebs-optimized")
                    if instance.get("NetworkInfo", {}).get("EnaSupportInfo", {}).get("Supported"):
                        features.add("ena")
                    if instance.get("ProcessorInfo", {}).get("SupportedArchitectures", []):
                        features.update(a.lower() for a in instance["ProcessorInfo"]["SupportedArchitectures"])

                    # Create instance type
                    instances.append(
                        VmInstanceType(
                            provider=CloudProvider.AWS,
                            instance_type=instance["InstanceType"],
                            vcpus=instance["VCpuInfo"]["DefaultVCpus"],
                            memory_gb=instance["MemoryInfo"]["SizeInMiB"] / 1024,
                            gpu_count=sum(
                                acc.get("Count", 0)
                                for acc in instance.get("GpuInfo", {}).get("Gpus", [])
                            ),
                            gpu_type=next(
                                (
                                    acc.get("Name")
                                    for acc in instance.get("GpuInfo", {}).get("Gpus", [])
                                ),
                                None,
                            ),
                            local_disk_gb=sum(
                                disk.get("SizeInGB", 0)
                                for disk in instance.get("InstanceStorageInfo", {}).get("Disks", [])
                            ),
                            network_bandwidth_gbps=(
                                instance.get("NetworkInfo", {}).get("NetworkPerformance", "").split(" ")[0]
                                if instance.get("NetworkInfo", {}).get("NetworkPerformance", "").endswith("Gbps")
                                else None
                            ),
                            features=features,
                        )
                    )

            return instances

        except (BotoCoreError, ClientError) as e:
            raise ProviderError(
                f"Failed to list AWS instance types: {str(e)}",
                provider="aws",
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
            # Get pricing filters
            offering_class, term_type = self.PURCHASE_OPTION_MAPPING[purchase_option]
            platform = self.OS_MAPPING[operating_system]

            # Get pricing
            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                    {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": platform},
                    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                    {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
                ],
            )

            if not response["PriceList"]:
                raise PricingError(
                    f"No pricing found for instance type {instance_type}",
                    provider="aws",
                    region=region,
                    instance_type=instance_type,
                )

            # Parse pricing data
            price_list = response["PriceList"][0]
            terms = price_list["terms"][offering_class]
            rate_code = next(iter(terms))
            price_dimensions = terms[rate_code]["priceDimensions"]
            price_dimension = next(iter(price_dimensions.values()))

            # Get hourly rate
            hourly_rate = Decimal(price_dimension["pricePerUnit"]["USD"])

            return CostComponent(
                name="Compute",
                hourly_cost=hourly_rate,
                monthly_cost=hourly_rate * 730,  # Average hours per month
            )

        except (BotoCoreError, ClientError) as e:
            raise PricingError(
                f"Failed to get AWS pricing: {str(e)}",
                provider="aws",
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
            # Get EBS pricing
            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                    {"Type": "TERM_MATCH", "Field": "volumeType", "Value": "General Purpose"},
                    {"Type": "TERM_MATCH", "Field": "volumeApiName", "Value": "gp2"},
                ],
            )

            if not response["PriceList"]:
                raise PricingError(
                    "No EBS pricing found",
                    provider="aws",
                    region=region,
                    instance_type=instance_type,
                )

            # Parse pricing data
            price_list = response["PriceList"][0]
            terms = price_list["terms"]["OnDemand"]
            rate_code = next(iter(terms))
            price_dimensions = terms[rate_code]["priceDimensions"]
            price_dimension = next(iter(price_dimensions.values()))

            # Get GB-month rate
            gb_month_rate = Decimal(price_dimension["pricePerUnit"]["USD"])
            monthly_cost = gb_month_rate * Decimal(str(storage_gb))
            hourly_cost = monthly_cost / 730  # Average hours per month

            return CostComponent(
                name="Storage",
                hourly_cost=hourly_cost,
                monthly_cost=monthly_cost,
            )

        except (BotoCoreError, ClientError) as e:
            raise PricingError(
                f"Failed to get AWS storage pricing: {str(e)}",
                provider="aws",
                region=region,
                instance_type=instance_type,
            ) from e
