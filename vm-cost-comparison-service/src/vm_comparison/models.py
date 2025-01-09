"""Data models for VM cost comparison.

This module provides data models for comparing virtual machine costs
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


class OperatingSystem(str, Enum):
    """Supported operating systems."""
    LINUX = "linux"
    WINDOWS = "windows"
    RHEL = "rhel"
    SUSE = "suse"
    UBUNTU = "ubuntu"


class PurchaseOption(str, Enum):
    """VM purchase options."""
    ON_DEMAND = "on_demand"
    RESERVED_1_YEAR = "reserved_1_year"
    RESERVED_3_YEAR = "reserved_3_year"
    SPOT = "spot"


class VmSize(BaseModel):
    """Virtual machine size requirements."""
    vcpus: int = Field(gt=0)
    memory_gb: float = Field(gt=0)
    gpu_count: Optional[int] = Field(default=0, ge=0)
    gpu_type: Optional[str] = None
    local_disk_gb: Optional[float] = Field(default=0, ge=0)
    network_bandwidth_gbps: Optional[float] = Field(default=0, ge=0)

    @validator("memory_gb", "local_disk_gb", "network_bandwidth_gbps")
    def validate_non_negative_float(cls, v):
        """Validate float fields are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Value must be non-negative")
        return v


class VmRequirements(BaseModel):
    """Virtual machine requirements."""
    size: VmSize
    operating_system: OperatingSystem
    purchase_option: PurchaseOption = Field(default=PurchaseOption.ON_DEMAND)
    region: str
    availability_level: Optional[str] = None  # e.g., "99.9%", "99.99%"
    min_local_storage: Optional[int] = None
    min_network_bandwidth: Optional[float] = None
    required_features: Set[str] = Field(default_factory=set)  # e.g., "nvme", "nested-virtualization"
    required_certifications: Set[str] = Field(default_factory=set)  # e.g., "hipaa", "pci-dss"


class VmInstanceType(BaseModel):
    """Cloud provider VM instance type."""
    provider: CloudProvider
    instance_type: str  # e.g., "t3.xlarge", "Standard_D4s_v3"
    vcpus: int
    memory_gb: float
    gpu_count: Optional[int] = 0
    gpu_type: Optional[str] = None
    local_disk_gb: Optional[float] = 0
    network_bandwidth_gbps: Optional[float] = 0
    features: Set[str] = Field(default_factory=set)
    certifications: Set[str] = Field(default_factory=set)


class CostComponent(BaseModel):
    """Individual cost component."""
    name: str  # e.g., "Compute", "Storage", "Network"
    hourly_cost: Decimal
    monthly_cost: Decimal
    details: Optional[Dict[str, str]] = None


class VmCostEstimate(BaseModel):
    """Cost estimate for a VM instance type."""
    provider: CloudProvider
    region: str
    instance_type: str
    operating_system: OperatingSystem
    purchase_option: PurchaseOption
    hourly_cost: Decimal
    monthly_cost: Decimal
    upfront_cost: Optional[Decimal] = None
    cost_components: List[CostComponent] = Field(default_factory=list)
    savings_plan_eligible: bool = False
    spot_price_history: Optional[Dict[str, List[Decimal]]] = None  # timestamp -> price
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class VmComparison(BaseModel):
    """Comparison of VM options across providers."""
    requirements: VmRequirements
    estimates: List[VmCostEstimate]
    recommended_option: Optional[VmCostEstimate] = None
    comparison_date: datetime = Field(default_factory=datetime.utcnow)
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notes: Optional[str] = None


class CostFactor(str, Enum):
    """Cost factors for VM pricing."""
    COMPUTE = "compute"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    OS_LICENSE = "os_license"
    SUPPORT = "support"


class PricingTier(BaseModel):
    """Pricing tier for a cost factor."""
    factor: CostFactor
    min_value: float  # e.g., min vCPUs or min GB
    max_value: Optional[float] = None  # None means unlimited
    unit_price: Decimal  # Price per unit (e.g., per vCPU or per GB)
    unit: str  # e.g., "vCPU", "GB", "GB/month"


class RegionalPricing(BaseModel):
    """Regional pricing information."""
    provider: CloudProvider
    region: str
    tiers: List[PricingTier]
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    currency: str = Field(default="USD")
    notes: Optional[str] = None


class ComparisonFilter(BaseModel):
    """Filter criteria for VM comparisons."""
    providers: Optional[Set[CloudProvider]] = None
    regions: Optional[Set[str]] = None
    min_vcpus: Optional[int] = None
    max_vcpus: Optional[int] = None
    min_memory_gb: Optional[float] = None
    max_memory_gb: Optional[float] = None
    operating_systems: Optional[Set[OperatingSystem]] = None
    purchase_options: Optional[Set[PurchaseOption]] = None
    required_features: Optional[Set[str]] = None
    required_certifications: Optional[Set[str]] = None
    max_hourly_cost: Optional[Decimal] = None
    max_monthly_cost: Optional[Decimal] = None


class ComparisonResult(BaseModel):
    """Result of a VM cost comparison."""
    comparison: VmComparison
    filters_applied: ComparisonFilter
    total_options_considered: int
    filtered_options_count: int
    processing_time_ms: float
    cache_hit: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = None
