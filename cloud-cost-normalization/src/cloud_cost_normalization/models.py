"""Data models for cloud cost normalization.

This module provides standardized data models for representing cloud costs
across different providers (AWS, Azure, GCP) in a normalized format.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


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


class BillingType(str, Enum):
    """Common billing types across cloud providers."""
    ON_DEMAND = "on_demand"
    RESERVED = "reserved"
    SPOT = "spot"
    SAVINGS_PLAN = "savings_plan"
    COMMITTED_USE = "committed_use"


class CostAllocation(BaseModel):
    """Model for cost allocation data."""
    project: Optional[str] = None
    department: Optional[str] = None
    environment: Optional[str] = None
    cost_center: Optional[str] = None
    team: Optional[str] = None
    application: Optional[str] = None
    custom_tags: Dict[str, str] = Field(default_factory=dict)


class ResourceMetadata(BaseModel):
    """Model for resource-specific metadata."""
    provider: CloudProvider
    provider_id: str
    name: str
    type: ResourceType
    region: str
    zone: Optional[str] = None
    billing_type: BillingType = BillingType.ON_DEMAND
    specifications: Dict[str, Union[str, int, float]] = Field(default_factory=dict)


class UsageData(BaseModel):
    """Model for resource usage data."""
    metric: str
    quantity: Decimal
    unit: str
    start_time: datetime
    end_time: datetime


class CostBreakdown(BaseModel):
    """Model for detailed cost breakdown."""
    compute: Decimal = Field(default=Decimal("0"))
    storage: Decimal = Field(default=Decimal("0"))
    network: Decimal = Field(default=Decimal("0"))
    license: Decimal = Field(default=Decimal("0"))
    support: Decimal = Field(default=Decimal("0"))
    other: Decimal = Field(default=Decimal("0"))

    @validator("*")
    def validate_amounts(cls, v: Decimal) -> Decimal:
        """Ensure all amounts are non-negative."""
        if v < 0:
            raise ValueError("Cost amounts cannot be negative")
        return v

    @property
    def total(self) -> Decimal:
        """Calculate total cost."""
        return (
            self.compute +
            self.storage +
            self.network +
            self.license +
            self.support +
            self.other
        )


class NormalizedCostEntry(BaseModel):
    """Normalized cost entry that can represent costs from any cloud provider."""
    id: str = Field(description="Unique identifier for the cost entry")
    account_id: str = Field(description="Cloud provider account identifier")
    resource: ResourceMetadata
    allocation: CostAllocation
    usage: List[UsageData] = Field(default_factory=list)
    cost_breakdown: CostBreakdown
    currency: str = Field(description="ISO 4217 currency code")
    start_time: datetime
    end_time: datetime
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Ensure currency code is uppercase and valid."""
        v = v.upper()
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost for this entry."""
        return self.cost_breakdown.total


class CostNormalizationResult(BaseModel):
    """Result of a cost normalization operation."""
    entries: List[NormalizedCostEntry]
    source_provider: CloudProvider
    target_currency: str
    start_time: datetime
    end_time: datetime
    total_cost: Decimal
    error_count: int = 0
    warnings: List[str] = Field(default_factory=list)

    @validator("target_currency")
    def validate_currency(cls, v: str) -> str:
        """Ensure currency code is uppercase and valid."""
        v = v.upper()
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v


class ResourceMapping(BaseModel):
    """Mapping between provider-specific and normalized resource types."""
    provider: CloudProvider
    provider_type: str
    normalized_type: ResourceType
    metadata_mapping: Dict[str, str] = Field(default_factory=dict)


class CurrencyConversion(BaseModel):
    """Model for currency conversion data."""
    source_currency: str
    target_currency: str
    exchange_rate: Decimal
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "forex-python"  # Source of exchange rate data

    @validator("exchange_rate")
    def validate_rate(cls, v: Decimal) -> Decimal:
        """Ensure exchange rate is positive."""
        if v <= 0:
            raise ValueError("Exchange rate must be positive")
        return v


class CostAggregation(BaseModel):
    """Model for aggregated cost data."""
    group_by: List[str]
    time_period: str
    costs: Dict[str, Decimal]
    resource_counts: Dict[str, int]
    total_cost: Decimal
    currency: str
    start_time: datetime
    end_time: datetime
