"""AWS Cost Explorer client package."""

from importlib import metadata

from .client import AWSCostExplorerClient
from .exceptions import (
    APIError,
    AuthenticationError,
    CacheError,
    ConfigurationError,
    CredentialsError,
    DataNotFoundError,
    InvalidDateRangeError,
    InvalidFilterError,
    InvalidGroupingError,
    InvalidMetricError,
    RateLimitError,
    RegionError,
    RetryError,
    ServiceQuotaExceededError,
    SessionError,
)
from .models import (
    CostFilter,
    CostReport,
    DateInterval,
    Expression,
    GetCostAndUsageRequest,
    GetCostForecastRequest,
    GetReservationUtilizationRequest,
    GetSavingsPlansUtilizationRequest,
    Granularity,
    GroupDefinition,
    GroupDefinitionType,
    MetricName,
    MetricValue,
    MetricValues,
    ReservationUtilization,
    SavingsPlanUtilization,
    TimeUnit,
)

try:
    __version__ = metadata.version("aws-cost-explorer-client")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0.dev0"

__all__ = [
    # Main client
    "AWSCostExplorerClient",
    
    # Models
    "CostFilter",
    "CostReport",
    "DateInterval",
    "Expression",
    "GetCostAndUsageRequest",
    "GetCostForecastRequest",
    "GetReservationUtilizationRequest",
    "GetSavingsPlansUtilizationRequest",
    "Granularity",
    "GroupDefinition",
    "GroupDefinitionType",
    "MetricName",
    "MetricValue",
    "MetricValues",
    "ReservationUtilization",
    "SavingsPlanUtilization",
    "TimeUnit",
    
    # Exceptions
    "APIError",
    "AuthenticationError",
    "CacheError",
    "ConfigurationError",
    "CredentialsError",
    "DataNotFoundError",
    "InvalidDateRangeError",
    "InvalidFilterError",
    "InvalidGroupingError",
    "InvalidMetricError",
    "RateLimitError",
    "RegionError",
    "RetryError",
    "ServiceQuotaExceededError",
    "SessionError",
]
