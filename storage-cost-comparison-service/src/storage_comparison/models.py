"""Data models for storage cost comparison.

This module provides data models for comparing storage costs
across different cloud providers (AWS, Azure, GCP).
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, validator


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class StorageClass(str, Enum):
    """Storage classes/tiers across providers."""
    # Hot storage
    STANDARD = "standard"  # AWS S3 Standard, Azure Hot, GCP Standard
    INFREQUENT = "infrequent"  # AWS S3 IA, Azure Cool, GCP Nearline
    ARCHIVE = "archive"  # AWS Glacier, Azure Archive, GCP Coldline
    DEEP_ARCHIVE = "deep_archive"  # AWS Glacier Deep Archive, GCP Archive

    # Performance storage
    PREMIUM = "premium"  # Azure Premium, GCP Premium
    PROVISIONED = "provisioned"  # AWS Provisioned IOPS

    # Region-specific
    ONE_ZONE = "one_zone"  # AWS One Zone-IA
    INTELLIGENT = "intelligent"  # Azure Intelligent-Tiering


class StorageType(str, Enum):
    """Types of storage services."""
    OBJECT = "object"  # S3, Blob Storage, Cloud Storage
    BLOCK = "block"  # EBS, Managed Disks, Persistent Disk
    FILE = "file"  # EFS, Files, Filestore


class ReplicationType(str, Enum):
    """Data replication options."""
    NONE = "none"
    LRS = "locally_redundant"  # Single region, multiple zones
    ZRS = "zone_redundant"  # Multiple zones
    GRS = "geo_redundant"  # Multiple regions
    RA_GRS = "read_access_geo_redundant"  # Multi-region with read access


class AccessTier(str, Enum):
    """Access patterns for storage."""
    HOT = "hot"  # Frequently accessed
    COOL = "cool"  # Infrequently accessed
    COLD = "cold"  # Rarely accessed
    ARCHIVE = "archive"  # Long-term retention


class PerformanceTier(str, Enum):
    """Performance tiers for block storage."""
    STANDARD = "standard"
    BALANCED = "balanced"
    PERFORMANCE = "performance"
    ULTRA = "ultra"


class StorageRequirements(BaseModel):
    """Storage requirements for comparison."""
    storage_type: StorageType
    capacity_gb: float = Field(gt=0)
    access_tier: Optional[AccessTier] = None
    replication_type: Optional[ReplicationType] = None
    performance_tier: Optional[PerformanceTier] = None
    region: str
    iops: Optional[int] = None
    throughput_mbps: Optional[float] = None
    required_features: Set[str] = Field(default_factory=set)  # e.g., "encryption", "versioning"
    required_certifications: Set[str] = Field(default_factory=set)  # e.g., "hipaa", "pci"

    @validator("capacity_gb")
    def validate_capacity(cls, v):
        """Validate storage capacity."""
        if v <= 0:
            raise ValueError("Capacity must be greater than 0")
        return v

    @validator("iops")
    def validate_iops(cls, v):
        """Validate IOPS if specified."""
        if v is not None and v <= 0:
            raise ValueError("IOPS must be greater than 0")
        return v

    @validator("throughput_mbps")
    def validate_throughput(cls, v):
        """Validate throughput if specified."""
        if v is not None and v <= 0:
            raise ValueError("Throughput must be greater than 0")
        return v


class StorageOption(BaseModel):
    """Storage option from a provider."""
    provider: CloudProvider
    storage_type: StorageType
    storage_class: StorageClass
    replication_type: ReplicationType
    region: str
    min_capacity_gb: float
    max_capacity_gb: Optional[float] = None
    min_iops: Optional[int] = None
    max_iops: Optional[int] = None
    min_throughput_mbps: Optional[float] = None
    max_throughput_mbps: Optional[float] = None
    features: Set[str] = Field(default_factory=set)
    certifications: Set[str] = Field(default_factory=set)


class CostComponent(BaseModel):
    """Individual cost component."""
    name: str  # e.g., "Storage", "IOPS", "Throughput"
    monthly_cost: Decimal
    details: Optional[Dict[str, str]] = None


class StorageCostEstimate(BaseModel):
    """Cost estimate for a storage option."""
    provider: CloudProvider
    storage_type: StorageType
    storage_class: StorageClass
    replication_type: ReplicationType
    region: str
    capacity_gb: float
    monthly_cost: Decimal
    cost_components: List[CostComponent] = Field(default_factory=list)
    features: Set[str] = Field(default_factory=set)
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class StorageComparison(BaseModel):
    """Comparison of storage options across providers."""
    requirements: StorageRequirements
    estimates: List[StorageCostEstimate]
    recommended_option: Optional[StorageCostEstimate] = None
    comparison_date: datetime = Field(default_factory=datetime.utcnow)
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notes: Optional[str] = None


class ComparisonFilter(BaseModel):
    """Filter criteria for storage comparisons."""
    providers: Optional[Set[CloudProvider]] = None
    storage_types: Optional[Set[StorageType]] = None
    storage_classes: Optional[Set[StorageClass]] = None
    replication_types: Optional[Set[ReplicationType]] = None
    regions: Optional[Set[str]] = None
    min_capacity_gb: Optional[float] = None
    max_capacity_gb: Optional[float] = None
    min_iops: Optional[int] = None
    max_iops: Optional[int] = None
    min_throughput_mbps: Optional[float] = None
    max_throughput_mbps: Optional[float] = None
    required_features: Optional[Set[str]] = None
    required_certifications: Optional[Set[str]] = None
    max_monthly_cost: Optional[Decimal] = None


class ComparisonResult(BaseModel):
    """Result of a storage cost comparison."""
    comparison: StorageComparison
    filters_applied: ComparisonFilter
    total_options_considered: int
    filtered_options_count: int
    processing_time_ms: float
    cache_hit: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = None


class PricingTier(BaseModel):
    """Pricing tier for storage costs."""
    min_gb: float
    max_gb: Optional[float] = None
    price_per_gb: Decimal
    conditions: Optional[Dict[str, str]] = None


class OperationalMetrics(BaseModel):
    """Operational metrics for storage options."""
    availability_sla: str  # e.g., "99.99%"
    durability_sla: str  # e.g., "99.999999999%"
    latency_ms: Optional[float] = None
    max_request_rate: Optional[int] = None
    max_capacity_tb: Optional[float] = None
    backup_included: bool = False
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
