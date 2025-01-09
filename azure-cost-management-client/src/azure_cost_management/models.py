"""Data models for Azure Cost Management client."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TimeframeType(str, Enum):
    """Time frame types for cost queries."""

    CUSTOM = "Custom"
    MONTH_TO_DATE = "MonthToDate"
    BILLING_MONTH_TO_DATE = "BillingMonthToDate"
    THE_LAST_BILLING_MONTH = "TheLastBillingMonth"
    THE_LAST_MONTH = "TheLastMonth"
    WEEK_TO_DATE = "WeekToDate"
    BILLING_WEEK_TO_DATE = "BillingWeekToDate"


class GranularityType(str, Enum):
    """Granularity for cost data."""

    DAILY = "Daily"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"


class MetricType(str, Enum):
    """Available cost metrics."""

    ACTUAL_COST = "ActualCost"
    AMORTIZED_COST = "AmortizedCost"
    USAGE_QUANTITY = "UsageQuantity"
    NORMALIZED_USAGE_AMOUNT = "NormalizedUsageAmount"


class GroupingDimension(str, Enum):
    """Dimensions for grouping cost data."""

    SUBSCRIPTION_ID = "SubscriptionId"
    RESOURCE_GROUP = "ResourceGroup"
    RESOURCE_TYPE = "ResourceType"
    RESOURCE_ID = "ResourceId"
    RESOURCE_LOCATION = "ResourceLocation"
    METER = "Meter"
    METER_CATEGORY = "MeterCategory"
    METER_SUBCATEGORY = "MeterSubCategory"
    SERVICE_NAME = "ServiceName"
    SERVICE_TIER = "ServiceTier"
    INVOICE_ID = "InvoiceId"
    CHARGE_TYPE = "ChargeType"
    PUBLISHER_TYPE = "PublisherType"
    RESERVATION_ID = "ReservationId"
    RESERVATION_NAME = "ReservationName"


class FilterType(str, Enum):
    """Types of filters for cost queries."""

    DIMENSION = "Dimension"
    TAG = "Tag"


class QueryTimeframe(BaseModel):
    """Time frame for cost queries."""

    from_date: Optional[datetime] = Field(None, alias="from")
    to_date: Optional[datetime] = None
    timeframe: Optional[TimeframeType] = None

    @validator("to_date")
    def validate_dates(cls, v: Optional[datetime], values: Dict) -> Optional[datetime]:
        """Validate date range."""
        if v and "from_date" in values and values["from_date"]:
            if v <= values["from_date"]:
                raise ValueError("to_date must be after from_date")
        return v


class QueryFilter(BaseModel):
    """Filter for cost queries."""

    type: FilterType
    name: str
    operator: str
    values: List[str]


class QueryGrouping(BaseModel):
    """Grouping configuration for cost queries."""

    type: GroupingDimension
    name: Optional[str] = None


class MetricConfiguration(BaseModel):
    """Configuration for cost metrics."""

    name: MetricType
    function: Optional[str] = None


class QueryDataset(BaseModel):
    """Dataset configuration for cost queries."""

    granularity: GranularityType
    aggregation: Dict[str, MetricConfiguration]
    grouping: Optional[List[QueryGrouping]] = None
    filter: Optional[QueryFilter] = None


class CostQueryDefinition(BaseModel):
    """Cost query definition."""

    type: str = "Usage"
    timeframe: Optional[TimeframeType] = None
    time_period: Optional[QueryTimeframe] = None
    dataset: QueryDataset


class MetricValue(BaseModel):
    """Value for a cost metric."""

    amount: Decimal
    currency: str


class CostRow(BaseModel):
    """Row of cost data."""

    metrics: Dict[str, MetricValue]
    grouping_values: Optional[Dict[str, str]] = None


class CostQueryResult(BaseModel):
    """Result of a cost query."""

    id: str
    name: str
    type: str
    rows: List[CostRow]
    total_cost: MetricValue


class ForecastDefinition(BaseModel):
    """Forecast query definition."""

    type: str = "Forecast"
    timeframe: TimeframeType
    time_period: Optional[QueryTimeframe] = None
    dataset: QueryDataset
    confidence_level: Optional[int] = Field(None, ge=1, le=99)


class ForecastResult(BaseModel):
    """Result of a forecast query."""

    id: str
    name: str
    type: str
    rows: List[CostRow]
    total_forecast: MetricValue
    confidence_intervals: Optional[List[Dict[str, MetricValue]]] = None


class BudgetTimeGrain(str, Enum):
    """Time grain for budgets."""

    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"


class BudgetFilter(BaseModel):
    """Filter for budgets."""

    dimensions: Optional[Dict[str, List[str]]] = None
    tags: Optional[Dict[str, List[str]]] = None
    resource_groups: Optional[List[str]] = None
    meters: Optional[List[str]] = None


class NotificationThreshold(BaseModel):
    """Notification threshold for budgets."""

    threshold_type: str
    threshold: Decimal = Field(ge=0, le=1000)
    operator: str
    notification_enabled: bool = True
    emails: Optional[List[str]] = None
    webhook_url: Optional[str] = None


class BudgetDefinition(BaseModel):
    """Budget definition."""

    name: str
    amount: Decimal
    time_grain: BudgetTimeGrain
    time_period: QueryTimeframe
    filter: Optional[BudgetFilter] = None
    notifications: Optional[Dict[str, NotificationThreshold]] = None


class BudgetStatus(BaseModel):
    """Budget status."""

    id: str
    name: str
    amount: MetricValue
    current_spend: MetricValue
    forecasted_spend: Optional[MetricValue] = None
    time_grain: BudgetTimeGrain
    time_period: QueryTimeframe
    notifications: Dict[str, NotificationThreshold]


# Request Models
class GetCostRequest(BaseModel):
    """Request parameters for getting cost data."""

    scope: str
    query: CostQueryDefinition


class GetForecastRequest(BaseModel):
    """Request parameters for getting cost forecast."""

    scope: str
    query: ForecastDefinition


class CreateBudgetRequest(BaseModel):
    """Request parameters for creating a budget."""

    scope: str
    budget_name: str
    budget: BudgetDefinition


class UpdateBudgetRequest(BaseModel):
    """Request parameters for updating a budget."""

    scope: str
    budget_name: str
    budget: BudgetDefinition


class DeleteBudgetRequest(BaseModel):
    """Request parameters for deleting a budget."""

    scope: str
    budget_name: str


class ListBudgetsRequest(BaseModel):
    """Request parameters for listing budgets."""

    scope: str
    filter: Optional[str] = None
    top: Optional[int] = Field(None, ge=1, le=1000)
    skip: Optional[int] = Field(None, ge=0)
