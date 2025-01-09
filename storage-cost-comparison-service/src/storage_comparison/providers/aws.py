"""AWS storage provider implementation.

This module provides functionality for retrieving AWS storage information
and pricing data for S3, EBS, and EFS.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set

import boto3
from botocore.exceptions import BotoCoreError, ClientError

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


class AwsStorageProvider:
    """Provider for AWS storage information and pricing."""

    # Maps our storage classes to AWS storage class values
    STORAGE_CLASS_MAPPING = {
        # S3 storage classes
        StorageClass.STANDARD: "Standard",
        StorageClass.INFREQUENT: "Standard-IA",
        StorageClass.ARCHIVE: "Glacier",
        StorageClass.DEEP_ARCHIVE: "Glacier Deep Archive",
        StorageClass.ONE_ZONE: "One Zone-IA",
        StorageClass.INTELLIGENT: "Intelligent-Tiering",

        # EBS volume types
        StorageClass.PREMIUM: "io2",  # Provisioned IOPS SSD
        StorageClass.PROVISIONED: "io2",  # Provisioned IOPS SSD
    }

    # Maps our replication types to AWS replication configurations
    REPLICATION_MAPPING = {
        ReplicationType.NONE: None,
        ReplicationType.LRS: "same-region",
        ReplicationType.ZRS: "multi-az",
        ReplicationType.GRS: "cross-region",
        ReplicationType.RA_GRS: "cross-region-read-replica",
    }

    # Features by storage class
    STORAGE_FEATURES = {
        # S3 features
        "Standard": {
            "versioning", "encryption", "replication", "lifecycle", 
            "object-lock", "inventory", "analytics"
        },
        "Standard-IA": {
            "versioning", "encryption", "replication", "lifecycle",
            "object-lock", "inventory"
        },
        "One Zone-IA": {
            "versioning", "encryption", "lifecycle", "inventory"
        },
        "Glacier": {
            "encryption", "lifecycle", "vault-lock"
        },
        "Glacier Deep Archive": {
            "encryption", "lifecycle", "vault-lock"
        },
        "Intelligent-Tiering": {
            "versioning", "encryption", "replication", "lifecycle",
            "object-lock", "inventory", "auto-tiering"
        },

        # EBS features
        "gp2": {"encryption", "snapshots", "multi-attach"},
        "gp3": {"encryption", "snapshots", "multi-attach"},
        "io1": {"encryption", "snapshots", "multi-attach", "provisioned-iops"},
        "io2": {"encryption", "snapshots", "multi-attach", "provisioned-iops"},
        "st1": {"encryption", "snapshots"},
        "sc1": {"encryption", "snapshots"},

        # EFS features
        "EFS Standard": {
            "encryption", "lifecycle", "backup", "replication",
            "access-points", "multi-az"
        },
        "EFS One Zone": {
            "encryption", "lifecycle", "backup", "access-points"
        },
    }

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str,
    ):
        """Initialize AWS storage provider.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region
        """
        self.region = region
        
        # Initialize clients
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )
        self.ec2_client = boto3.client(
            "ec2",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )
        self.efs_client = boto3.client(
            "efs",
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

    async def list_storage_options(
        self,
        storage_type: StorageType,
        region: Optional[str] = None,
    ) -> List[StorageOption]:
        """List available AWS storage options.

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
                # S3 storage classes
                options.extend([
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.ZRS,  # S3 Standard is multi-AZ by default
                        region=region,
                        min_capacity_gb=0,  # No minimum
                        max_capacity_gb=None,  # No maximum
                        features=self.STORAGE_FEATURES["Standard"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.INFREQUENT,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=128 / 1024,  # 128 KB minimum object size
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["Standard-IA"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.ONE_ZONE,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=128 / 1024,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["One Zone-IA"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.ARCHIVE,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=40 / 1024,  # 40 KB minimum
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["Glacier"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.DEEP_ARCHIVE,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=40 / 1024,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["Glacier Deep Archive"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.OBJECT,
                        storage_class=StorageClass.INTELLIGENT,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["Intelligent-Tiering"],
                    ),
                ])

            elif storage_type == StorageType.BLOCK:
                # EBS volume types
                options.extend([
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.STANDARD,  # gp2/gp3
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=1,
                        max_capacity_gb=16384,  # 16 TiB
                        min_iops=3000,
                        max_iops=16000,
                        min_throughput_mbps=125,
                        max_throughput_mbps=1000,
                        features=self.STORAGE_FEATURES["gp3"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.BLOCK,
                        storage_class=StorageClass.PREMIUM,  # io2
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=4,
                        max_capacity_gb=16384,
                        min_iops=100,
                        max_iops=64000,
                        min_throughput_mbps=125,
                        max_throughput_mbps=1000,
                        features=self.STORAGE_FEATURES["io2"],
                    ),
                ])

            elif storage_type == StorageType.FILE:
                # EFS file systems
                options.extend([
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.FILE,
                        storage_class=StorageClass.STANDARD,
                        replication_type=ReplicationType.ZRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["EFS Standard"],
                    ),
                    StorageOption(
                        provider=CloudProvider.AWS,
                        storage_type=StorageType.FILE,
                        storage_class=StorageClass.ONE_ZONE,
                        replication_type=ReplicationType.LRS,
                        region=region,
                        min_capacity_gb=0,
                        max_capacity_gb=None,
                        features=self.STORAGE_FEATURES["EFS One Zone"],
                    ),
                ])

            return options

        except (BotoCoreError, ClientError) as e:
            raise ProviderError(
                f"Failed to list AWS storage options: {str(e)}",
                provider="aws",
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
            # Get pricing filters
            aws_storage_class = self.STORAGE_CLASS_MAPPING[storage_class]

            if storage_type == StorageType.OBJECT:
                # Get S3 pricing
                filters = [
                    {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Storage"},
                    {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                    {"Type": "TERM_MATCH", "Field": "storageClass", "Value": aws_storage_class},
                ]
                service_code = "AmazonS3"

            elif storage_type == StorageType.BLOCK:
                # Get EBS pricing
                filters = [
                    {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Storage"},
                    {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                    {"Type": "TERM_MATCH", "Field": "volumeApiName", "Value": aws_storage_class},
                ]
                service_code = "AmazonEC2"

            else:  # FILE
                # Get EFS pricing
                filters = [
                    {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Storage"},
                    {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                    {"Type": "TERM_MATCH", "Field": "storageClass", "Value": aws_storage_class},
                ]
                service_code = "AmazonEFS"

            # Get pricing data
            response = self.pricing_client.get_products(
                ServiceCode=service_code,
                Filters=filters,
            )

            if not response["PriceList"]:
                raise PricingError(
                    f"No pricing found for storage type {storage_type.value}",
                    provider="aws",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Parse pricing data
            price_list = response["PriceList"][0]
            terms = price_list["terms"]["OnDemand"]
            rate_code = next(iter(terms))
            price_dimensions = terms[rate_code]["priceDimensions"]
            price_dimension = next(iter(price_dimensions.values()))

            # Get monthly rate per GB
            gb_month_rate = Decimal(price_dimension["pricePerUnit"]["USD"])
            monthly_cost = gb_month_rate * Decimal(str(capacity_gb))

            return CostComponent(
                name="Storage",
                monthly_cost=monthly_cost,
            )

        except (BotoCoreError, ClientError) as e:
            raise PricingError(
                f"Failed to get AWS storage pricing: {str(e)}",
                provider="aws",
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
            # Get EBS IOPS pricing
            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "System Operation"},
                    {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                    {"Type": "TERM_MATCH", "Field": "volumeApiName", "Value": self.STORAGE_CLASS_MAPPING[storage_class]},
                ],
            )

            if not response["PriceList"]:
                raise PricingError(
                    "No IOPS pricing found",
                    provider="aws",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Parse pricing data
            price_list = response["PriceList"][0]
            terms = price_list["terms"]["OnDemand"]
            rate_code = next(iter(terms))
            price_dimensions = terms[rate_code]["priceDimensions"]
            price_dimension = next(iter(price_dimensions.values()))

            # Get monthly rate per IOPS
            iops_month_rate = Decimal(price_dimension["pricePerUnit"]["USD"])
            monthly_cost = iops_month_rate * Decimal(str(iops))

            return CostComponent(
                name="IOPS",
                monthly_cost=monthly_cost,
            )

        except (BotoCoreError, ClientError) as e:
            raise PricingError(
                f"Failed to get AWS IOPS pricing: {str(e)}",
                provider="aws",
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
            # Get EBS throughput pricing
            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Provisioned Throughput"},
                    {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                    {"Type": "TERM_MATCH", "Field": "volumeApiName", "Value": self.STORAGE_CLASS_MAPPING[storage_class]},
                ],
            )

            if not response["PriceList"]:
                raise PricingError(
                    "No throughput pricing found",
                    provider="aws",
                    region=region,
                    storage_type=storage_type.value,
                    storage_class=storage_class.value,
                )

            # Parse pricing data
            price_list = response["PriceList"][0]
            terms = price_list["terms"]["OnDemand"]
            rate_code = next(iter(terms))
            price_dimensions = terms[rate_code]["priceDimensions"]
            price_dimension = next(iter(price_dimensions.values()))

            # Get monthly rate per MB/s
            mbps_month_rate = Decimal(price_dimension["pricePerUnit"]["USD"])
            monthly_cost = mbps_month_rate * Decimal(str(throughput_mbps))

            return CostComponent(
                name="Throughput",
                monthly_cost=monthly_cost,
            )

        except (BotoCoreError, ClientError) as e:
            raise PricingError(
                f"Failed to get AWS throughput pricing: {str(e)}",
                provider="aws",
                region=region,
                storage_type=storage_type.value,
                storage_class=storage_class.value,
            ) from e
