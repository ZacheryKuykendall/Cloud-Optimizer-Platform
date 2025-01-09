"""Azure Cost Management client package."""

from importlib import metadata

from .client import AzureCostManagementClient
from .exceptions import (
    APIError,
    AuthenticationError,
    BudgetError,
    CacheError,
    ConfigurationError,
    CredentialsError,
    DataNotFoundError,
    InvalidFilterError,
    InvalidGroupingError,
    InvalidMetricError,
    InvalidScopeError,
    InvalidTimeframeError,
    RateLimitError,
    ResourceGroupError,
    RetryError,
    SubscriptionError,
)
from .models import (
    BudgetDefinition,
    BudgetFilter,
    BudgetStatus,
    BudgetTimeGrain,
    CostQueryDefinition,
    CostQueryResult,
    CostRow,
    CreateBudgetRequest,
    DeleteBudgetRequest,
    FilterType,
    ForecastDefinition,
    ForecastResult,
    GetCostRequest,
    GetForecastRequest,
    GranularityType,
    GroupingDimension,
    ListBudgetsRequest,
    MetricConfiguration,
    MetricType,
    MetricValue,
    NotificationThreshold,
    QueryDataset,
    QueryFilter,
    QueryGrouping,
    QueryTimeframe,
    TimeframeType,
    UpdateBudgetRequest,
)

try:
    __version__ = metadata.version("azure-cost-management-client")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0.dev0"

__all__ = [
    # Main client
    "AzureCostManagementClient",
    
    # Models
    "BudgetDefinition",
    "BudgetFilter",
    "BudgetStatus",
    "BudgetTimeGrain",
    "CostQueryDefinition",
    "CostQueryResult",
    "CostRow",
    "CreateBudgetRequest",
    "DeleteBudgetRequest",
    "FilterType",
    "ForecastDefinition",
    "ForecastResult",
    "GetCostRequest",
    "GetForecastRequest",
    "GranularityType",
    "GroupingDimension",
    "ListBudgetsRequest",
    "MetricConfiguration",
    "MetricType",
    "MetricValue",
    "NotificationThreshold",
    "QueryDataset",
    "QueryFilter",
    "QueryGrouping",
    "QueryTimeframe",
    "TimeframeType",
    "UpdateBudgetRequest",
    
    # Exceptions
    "APIError",
    "AuthenticationError",
    "BudgetError",
    "CacheError",
    "ConfigurationError",
    "CredentialsError",
    "DataNotFoundError",
    "InvalidFilterError",
    "InvalidGroupingError",
    "InvalidMetricError",
    "InvalidScopeError",
    "InvalidTimeframeError",
    "RateLimitError",
    "ResourceGroupError",
    "RetryError",
    "SubscriptionError",
]
