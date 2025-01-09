"""Cloud Cost Normalization Library

This library provides functionality for normalizing and standardizing cloud cost data
across different providers (AWS, Azure, GCP) with support for currency conversion
and cost data storage.
"""

from cloud_cost_normalization.models import (
    CloudProvider,
    ResourceType,
    BillingType,
    CostAllocation,
    ResourceMetadata,
    UsageData,
    CostBreakdown,
    NormalizedCostEntry,
    CostNormalizationResult,
    ResourceMapping,
    CurrencyConversion,
    CostAggregation,
)
from cloud_cost_normalization.currency import CurrencyService
from cloud_cost_normalization.exceptions import (
    CloudCostNormalizationError,
    ValidationError,
    CurrencyError,
    InvalidCurrencyError,
    CurrencyConversionError,
    RateNotFoundError,
    ProviderError,
    UnsupportedProviderError,
    ProviderAuthenticationError,
    ProviderAPIError,
    DataNormalizationError,
    ResourceMappingError,
    StorageError,
    ConfigurationError,
    CacheError,
    DateRangeError,
    AggregationError,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "CloudProvider",
    "ResourceType",
    "BillingType",
    "CostAllocation",
    "ResourceMetadata",
    "UsageData",
    "CostBreakdown",
    "NormalizedCostEntry",
    "CostNormalizationResult",
    "ResourceMapping",
    "CurrencyConversion",
    "CostAggregation",
    
    # Services
    "CurrencyService",
    
    # Exceptions
    "CloudCostNormalizationError",
    "ValidationError",
    "CurrencyError",
    "InvalidCurrencyError",
    "CurrencyConversionError",
    "RateNotFoundError",
    "ProviderError",
    "UnsupportedProviderError",
    "ProviderAuthenticationError",
    "ProviderAPIError",
    "DataNormalizationError",
    "ResourceMappingError",
    "StorageError",
    "ConfigurationError",
    "CacheError",
    "DateRangeError",
    "AggregationError",
]
