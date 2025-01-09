"""Data models for Terraform cost analysis.

This module provides data models for representing Terraform resources
and their associated cost estimates.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ResourceAction(str, Enum):
    """Terraform plan actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NO_CHANGE = "no-change"


class ResourceType(str, Enum):
    """Common resource types across cloud providers."""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    SERVERLESS = "serverless"
    CONTAINER = "container"
    ANALYTICS = "analytics"
    SECURITY = "security"
    MANAGEMENT = "management"
    OTHER = "other"


class PricingTier(str, Enum):
    """Common pricing tiers."""
    ON_DEMAND = "on_demand"
    RESERVED = "reserved"
    SPOT = "spot"
    SAVINGS_PLAN = "savings_plan"
    COMMITTED_USE = "committed_use"


class ResourceMetadata(BaseModel):
    """Metadata for a Terraform resource."""
    provider: CloudProvider
    type: str
    name: str
    normalized_type: ResourceType
    region: str
    pricing_tier: PricingTier = Field(default=PricingTier.ON_DEMAND)
    specifications: Dict[str, str] = Field(default_factory=dict)


class CostComponent(BaseModel):
    """Individual cost component for a resource."""
    name: str
    unit: str
    hourly_cost: Decimal
    monthly_cost: Decimal
    details: Dict[str, str] = Field(default_factory=dict)


class ResourceCost(BaseModel):
    """Cost estimate for a Terraform resource."""
    id: str = Field(description="Unique identifier for the resource")
    metadata: ResourceMetadata
    action: ResourceAction
    components: List[CostComponent] = Field(default_factory=list)
    hourly_cost: Decimal = Field(default=Decimal("0"))
    monthly_cost: Decimal = Field(default=Decimal("0"))
    currency: str = Field(default="USD")
    previous_cost: Optional[Decimal] = None
    cost_change: Optional[Decimal] = None
    usage_estimates: Dict[str, Decimal] = Field(default_factory=dict)


class ModuleCost(BaseModel):
    """Cost estimate for a Terraform module."""
    name: str
    resources: List[ResourceCost] = Field(default_factory=list)
    hourly_cost: Decimal = Field(default=Decimal("0"))
    monthly_cost: Decimal = Field(default=Decimal("0"))
    currency: str = Field(default="USD")
    previous_cost: Optional[Decimal] = None
    cost_change: Optional[Decimal] = None


class CostBreakdown(BaseModel):
    """Detailed cost breakdown by resource type."""
    compute: Decimal = Field(default=Decimal("0"))
    storage: Decimal = Field(default=Decimal("0"))
    database: Decimal = Field(default=Decimal("0"))
    network: Decimal = Field(default=Decimal("0"))
    serverless: Decimal = Field(default=Decimal("0"))
    container: Decimal = Field(default=Decimal("0"))
    analytics: Decimal = Field(default=Decimal("0"))
    security: Decimal = Field(default=Decimal("0"))
    management: Decimal = Field(default=Decimal("0"))
    other: Decimal = Field(default=Decimal("0"))

    @property
    def total(self) -> Decimal:
        """Calculate total cost."""
        return sum(
            [
                self.compute,
                self.storage,
                self.database,
                self.network,
                self.serverless,
                self.container,
                self.analytics,
                self.security,
                self.management,
                self.other,
            ]
        )


class CostSummary(BaseModel):
    """Summary of total costs and changes."""
    total_resources: int
    resources_to_add: int
    resources_to_update: int
    resources_to_delete: int
    total_hourly_cost: Decimal
    total_monthly_cost: Decimal
    previous_total_monthly_cost: Optional[Decimal] = None
    total_monthly_cost_change: Optional[Decimal] = None
    breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    currency: str = Field(default="USD")


class CostAnalysis(BaseModel):
    """Complete cost analysis for a Terraform plan."""
    project_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    provider_region_pairs: List[tuple[CloudProvider, str]]
    modules: List[ModuleCost] = Field(default_factory=list)
    resources: List[ResourceCost] = Field(default_factory=list)
    summary: CostSummary
    currency: str = Field(default="USD")
    metadata: Dict[str, str] = Field(default_factory=dict)


class ResourceMapping(BaseModel):
    """Mapping between Terraform and normalized resource types."""
    provider: CloudProvider
    terraform_type: str
    normalized_type: ResourceType
    pricing_tier: Optional[PricingTier] = None
    metadata_mapping: Dict[str, str] = Field(default_factory=dict)


class PricingData(BaseModel):
    """Pricing data for a resource type."""
    provider: CloudProvider
    resource_type: str
    region: str
    pricing_tier: PricingTier
    unit_price: Decimal
    unit: str
    currency: str
    effective_date: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)


class UsageEstimate(BaseModel):
    """Usage estimate for a resource."""
    resource_type: str
    metric: str
    quantity: Decimal
    unit: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    metadata: Dict[str, str] = Field(default_factory=dict)
