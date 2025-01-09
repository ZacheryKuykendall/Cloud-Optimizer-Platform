"""Currency Conversion Service

A service for handling currency conversions and exchange rates for cloud cost data.
Supports multiple rate providers, caching strategies, and batch operations.
"""

from currency_conversion.models import (
    RateSource,
    RateType,
    UpdateFrequency,
    CacheStrategy,
    Money,
    ExchangeRate,
    ConversionRequest,
    ConversionResult,
    RateProviderConfig,
    ConversionBatch,
    BatchResult,
    RateAlert,
    ConversionMetrics,
)
from currency_conversion.exceptions import (
    CurrencyConversionError,
    ValidationError,
    ConfigurationError,
    RateProviderError,
    RateLimitError,
    UnsupportedCurrencyError,
    NoExchangeRateError,
    StaleRateError,
    CacheError,
    BatchConversionError,
    AlertConfigurationError,
    DatabaseError,
    MetricsError,
    ProviderSyncError,
    InvalidOperationError,
)

__version__ = "0.1.0"

__all__ = [
    # Enums
    "RateSource",
    "RateType",
    "UpdateFrequency",
    "CacheStrategy",

    # Core Models
    "Money",
    "ExchangeRate",
    "ConversionRequest",
    "ConversionResult",
    "RateProviderConfig",

    # Batch Operations
    "ConversionBatch",
    "BatchResult",

    # Monitoring
    "RateAlert",
    "ConversionMetrics",

    # Base Exceptions
    "CurrencyConversionError",
    "ValidationError",
    "ConfigurationError",

    # Provider Exceptions
    "RateProviderError",
    "RateLimitError",
    "UnsupportedCurrencyError",
    "NoExchangeRateError",
    "StaleRateError",

    # Operation Exceptions
    "CacheError",
    "BatchConversionError",
    "AlertConfigurationError",
    "DatabaseError",
    "MetricsError",
    "ProviderSyncError",
    "InvalidOperationError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
