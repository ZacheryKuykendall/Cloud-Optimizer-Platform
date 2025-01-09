"""Data models for AWS Cost Explorer client."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TimeUnit(str, Enum):
    """Time unit for cost aggregation."""

    HOURLY = "HOURLY"
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    ANNUALLY = "ANNUALLY"


class Granularity(str, Enum):
    """Granularity for cost data."""

    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    HOURLY = "HOURLY"


class MetricName(str, Enum):
    """Available cost metrics."""

    AMORTIZED_COST = "AmortizedCost"
    BLENDED_COST = "BlendedCost"
    NET_AMORTIZED_COST = "NetAmortizedCost"
    NET_UNBLENDED_COST = "NetUnblendedCost"
    NORMALIZED_USAGE_AMOUNT = "NormalizedUsageAmount"
    UNBLENDED_COST = "UnblendedCost"
    USAGE_QUANTITY = "UsageQuantity"


class GroupDefinitionType(str, Enum):
    """Types of grouping for cost data."""

    AZ = "AZ"
    INSTANCE_TYPE = "INSTANCE_TYPE"
    LEGAL_ENTITY_NAME = "LEGAL_ENTITY_NAME"
    LINKED_ACCOUNT = "LINKED_ACCOUNT"
    OPERATION = "OPERATION"
    PLATFORM = "PLATFORM"
    PURCHASE_TYPE = "PURCHASE_TYPE"
    SERVICE = "SERVICE"
    TAGS = "TAG"
    TENANCY = "TENANCY"
    RECORD_TYPE = "RECORD_TYPE"
    USAGE_TYPE = "USAGE_TYPE"


class Expression(BaseModel):
    """Cost filter expression."""

    dimension: str
    values: List[str]
    operator: Optional[str] = None


class CostFilter(BaseModel):
    """Filter for cost queries."""

    expressions: List[Expression]


class GroupDefinition(BaseModel):
    """Definition for grouping cost data."""

    type: GroupDefinitionType
    key: Optional[str] = None  # Required for TAGS type


class DateInterval(BaseModel):
    """Date range for cost queries."""

    start: datetime
    end: datetime

    @validator("end")
    def end_after_start(cls, v: datetime, values: Dict) -> datetime:
        """Validate end date is after start date."""
        if "start" in values and v <= values["start"]:
            raise ValueError("end date must be after start date")
        return v


class MetricValue(BaseModel):
    """Value for a cost metric."""

    amount: Decimal
    unit: str


class MetricValues(BaseModel):
    """Collection of metric values."""

    amortized_cost: Optional[MetricValue]
    blended_cost: Optional[MetricValue]
    net_amortized_cost: Optional[MetricValue]
    net_unblended_cost: Optional[MetricValue]
    normalized_usage_amount: Optional[MetricValue]
    unblended_cost: Optional[MetricValue]
    usage_quantity: Optional[MetricValue]


class Group(BaseModel):
    """Group of cost data."""

    keys: List[str]
    metrics: MetricValues


class ResultByTime(BaseModel):
    """Cost data for a time period."""

    timestamp: datetime
    groups: List[Group]
    estimated: bool


class CostReport(BaseModel):
    """Complete cost report."""

    dimension_value_attributes: Optional[List[Dict]] = None
    groups: List[Group]
    next_page_token: Optional[str] = None
    results_by_time: List[ResultByTime]


class ReservationUtilization(BaseModel):
    """Reservation utilization data."""

    total_running_hours: int
    utilized_hours: int
    unused_hours: int
    utilization_percentage: Decimal

    @validator("utilization_percentage")
    def validate_percentage(cls, v: Decimal) -> Decimal:
        """Validate utilization percentage is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError("utilization percentage must be between 0 and 100")
        return v


class ReservationCoverage(BaseModel):
    """Reservation coverage data."""

    total_running_hours: int
    covered_hours: int
    uncovered_hours: int
    coverage_percentage: Decimal

    @validator("coverage_percentage")
    def validate_percentage(cls, v: Decimal) -> Decimal:
        """Validate coverage percentage is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError("coverage percentage must be between 0 and 100")
        return v


class SavingsPlanUtilization(BaseModel):
    """Savings Plan utilization data."""

    total_commitment: Decimal
    used_commitment: Decimal
    unused_commitment: Decimal
    utilization_percentage: Decimal

    @validator("utilization_percentage")
    def validate_percentage(cls, v: Decimal) -> Decimal:
        """Validate utilization percentage is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError("utilization percentage must be between 0 and 100")
        return v


class CostForecast(BaseModel):
    """Cost forecast data."""

    mean_value: Decimal
    prediction_interval_lower_bound: Decimal
    prediction_interval_upper_bound: Decimal
    prediction_interval_confidence_level: Decimal = Field(ge=0, le=100)


class CostAnomaly(BaseModel):
    """Cost anomaly data."""

    anomaly_id: str
    anomaly_score: Decimal = Field(ge=0, le=100)
    impact: Decimal
    root_cause: Dict[str, List[str]]
    timestamp: datetime


class Tag(BaseModel):
    """Resource tag."""

    key: str
    values: List[str]


class CostAllocationTag(BaseModel):
    """Cost allocation tag configuration."""

    tag_key: str
    status: str
    type: str  # AWS or User


class Budget(BaseModel):
    """Budget configuration."""

    budget_name: str
    budget_limit: MetricValue
    time_period: DateInterval
    time_unit: TimeUnit
    cost_filters: Optional[Dict[str, List[str]]] = None
    notifications: Optional[List[Dict]] = None


class CostCategory(BaseModel):
    """Cost category configuration."""

    name: str
    rule_version: str
    rules: List[Dict]
    split_charges_rules: Optional[List[Dict]] = None
    effective_start: datetime
    effective_end: Optional[datetime] = None


# Request Models
class GetCostAndUsageRequest(BaseModel):
    """Request parameters for GetCostAndUsage API."""

    time_period: DateInterval
    granularity: Granularity
    metrics: List[MetricName]
    group_by: Optional[List[GroupDefinition]] = None
    filter: Optional[CostFilter] = None
    next_page_token: Optional[str] = None


class GetReservationUtilizationRequest(BaseModel):
    """Request parameters for GetReservationUtilization API."""

    time_period: DateInterval
    granularity: Granularity
    group_by: Optional[List[GroupDefinition]] = None
    filter: Optional[CostFilter] = None


class GetSavingsPlansUtilizationRequest(BaseModel):
    """Request parameters for GetSavingsPlansUtilization API."""

    time_period: DateInterval
    granularity: Granularity
    group_by: Optional[List[GroupDefinition]] = None
    filter: Optional[CostFilter] = None


class GetCostForecastRequest(BaseModel):
    """Request parameters for GetCostForecast API."""

    time_period: DateInterval
    granularity: Granularity
    metric: MetricName
    prediction_interval_level: Optional[int] = Field(None, ge=0, le=100)


class GetAnomaliesRequest(BaseModel):
    """Request parameters for GetAnomalies API."""

    time_period: DateInterval
    threshold: Decimal = Field(ge=0)
    monitor_arn: Optional[str] = None
