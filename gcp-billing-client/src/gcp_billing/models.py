"""Data models for GCP Cloud Billing client."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TimeframeType(str, Enum):
    """Time frame types for billing queries."""

    CUSTOM = "CUSTOM"
    MONTH_TO_DATE = "MONTH_TO_DATE"
    LAST_MONTH = "LAST_MONTH"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"


class GranularityType(str, Enum):
    """Granularity for billing data."""

    DAILY = "DAILY"
    MONTHLY = "MONTHLY"


class ServiceType(str, Enum):
    """GCP service types."""

    COMPUTE_ENGINE = "Compute Engine"
    CLOUD_STORAGE = "Cloud Storage"
    CLOUD_SQL = "Cloud SQL"
    BIGQUERY = "BigQuery"
    KUBERNETES_ENGINE = "Kubernetes Engine"
    APP_ENGINE = "App Engine"
    CLOUD_FUNCTIONS = "Cloud Functions"
    CLOUD_RUN = "Cloud Run"
    ALL_SERVICES = "All Services"


class CostMetricType(str, Enum):
    """Available cost metrics."""

    COST = "cost"
    USAGE = "usage"
    CREDITS = "credits"
    ADJUSTMENTS = "adjustments"


class GroupingDimension(str, Enum):
    """Dimensions for grouping billing data."""

    PROJECT = "project"
    SERVICE = "service"
    SKU = "sku"
    LOCATION = "location"
    RESOURCE = "resource"
    INVOICE = "invoice"
    LABEL = "label"


class FilterType(str, Enum):
    """Types of filters for billing queries."""

    PROJECT = "project"
    SERVICE = "service"
    SKU = "sku"
    LOCATION = "location"
    RESOURCE = "resource"
    LABEL = "label"


class QueryTimeframe(BaseModel):
    """Time frame for billing queries."""

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
    """Filter for billing queries."""

    type: FilterType
    name: str
    values: List[str]


class QueryGrouping(BaseModel):
    """Grouping configuration for billing queries."""

    type: GroupingDimension
    name: Optional[str] = None


class MetricConfiguration(BaseModel):
    """Configuration for billing metrics."""

    name: CostMetricType
    aggregation: Optional[str] = None


class QueryDataset(BaseModel):
    """Dataset configuration for billing queries."""

    granularity: GranularityType
    metrics: List[MetricConfiguration]
    grouping: Optional[List[QueryGrouping]] = None
    filter: Optional[QueryFilter] = None


class BillingQueryDefinition(BaseModel):
    """Billing query definition."""

    time_period: QueryTimeframe
    dataset: QueryDataset


class MetricValue(BaseModel):
    """Value for a billing metric."""

    amount: Decimal
    currency: str
    unit: Optional[str] = None


class BillingRow(BaseModel):
    """Row of billing data."""

    metrics: Dict[str, MetricValue]
    grouping_values: Optional[Dict[str, str]] = None


class BillingQueryResult(BaseModel):
    """Result of a billing query."""

    rows: List[BillingRow]
    total_cost: MetricValue
    total_credits: Optional[MetricValue] = None
    total_adjustments: Optional[MetricValue] = None


class BudgetAlertThreshold(BaseModel):
    """Budget alert threshold configuration."""

    percent: Decimal = Field(ge=0, le=100)
    email_enabled: bool = True
    email_addresses: Optional[List[str]] = None
    pubsub_topic: Optional[str] = None


class BudgetAmount(BaseModel):
    """Budget amount configuration."""

    amount: Decimal
    currency: str = "USD"
    credit_types_treatment: Optional[str] = None


class BudgetFilter(BaseModel):
    """Filter for budgets."""

    projects: Optional[List[str]] = None
    services: Optional[List[str]] = None
    credit_types: Optional[List[str]] = None
    labels: Optional[Dict[str, List[str]]] = None


class BudgetDefinition(BaseModel):
    """Budget definition."""

    display_name: str
    amount: BudgetAmount
    time_period: QueryTimeframe
    filter: Optional[BudgetFilter] = None
    thresholds: Optional[Dict[str, BudgetAlertThreshold]] = None


class BudgetStatus(BaseModel):
    """Budget status."""

    name: str
    display_name: str
    amount: BudgetAmount
    current_spend: MetricValue
    forecasted_spend: Optional[MetricValue] = None
    alerts_triggered: Optional[List[str]] = None


# Request Models
class GetBillingDataRequest(BaseModel):
    """Request parameters for getting billing data."""

    billing_account: str
    query: BillingQueryDefinition


class CreateBudgetRequest(BaseModel):
    """Request parameters for creating a budget."""

    billing_account: str
    budget: BudgetDefinition


class UpdateBudgetRequest(BaseModel):
    """Request parameters for updating a budget."""

    name: str
    budget: BudgetDefinition


class DeleteBudgetRequest(BaseModel):
    """Request parameters for deleting a budget."""

    name: str


class ListBudgetsRequest(BaseModel):
    """Request parameters for listing budgets."""

    billing_account: str
    page_size: Optional[int] = Field(None, ge=1, le=1000)
    page_token: Optional[str] = None


class ExportDataRequest(BaseModel):
    """Request parameters for exporting billing data."""

    billing_account: str
    query: BillingQueryDefinition
    destination: str  # BigQuery table or Cloud Storage bucket
    format: str = "CSV"  # CSV, JSON, or NEWLINE_DELIMITED_JSON


class ExportStatus(BaseModel):
    """Status of a billing data export job."""

    name: str
    state: str
    destination: str
    create_time: datetime
    update_time: datetime
    error: Optional[str] = None


class PricingInfo(BaseModel):
    """Pricing information for a SKU."""

    effective_time: datetime
    summary: str
    pricing_expression: Dict[str, Any]
    aggregation_info: Optional[Dict[str, Any]] = None
    currency_conversion_rate: Optional[float] = None


class ServiceInfo(BaseModel):
    """Information about a GCP service."""

    name: str
    id: str
    display_name: str
    business_entity_name: Optional[str] = None


class SkuInfo(BaseModel):
    """Information about a SKU."""

    name: str
    sku_id: str
    description: str
    category: Optional[Dict[str, str]] = None
    pricing_info: List[PricingInfo]
    service_regions: List[str]
    business_entity_name: Optional[str] = None


class GetPricingRequest(BaseModel):
    """Request parameters for getting pricing information."""

    service: Optional[str] = None
    sku: Optional[str] = None
    region: Optional[str] = None
    effective_time: Optional[datetime] = None
