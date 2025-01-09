"""VM Cost Comparison Service

A service for comparing virtual machine costs across different cloud providers,
providing detailed cost analysis, performance metrics, and optimization recommendations.
"""

from vm_comparison.models import (
    # Cloud Providers and Categories
    CloudProvider,
    OperatingSystem,
    VMCategory,
    PricingModel,
    BillingTerm,

    # Core Models
    VMSpecs,
    VMRequirements,
    VMInstance,
    VMPricing,
    VMCostBreakdown,
    VMCostEstimate,

    # Comparison Models
    ComparisonCriteria,
    ComparisonResult,
    PerformanceMetrics,
    ComparisonRequest,
    ComparisonResponse,
)

from vm_comparison.exceptions import (
    # Base Exceptions
    VMComparisonError,
    ValidationError,
    ConfigurationError,

    # Provider and Instance Exceptions
    ProviderError,
    PricingError,
    InstanceNotFoundError,
    RequirementsNotMetError,

    # Comparison Exceptions
    ComparisonError,
    PerformanceDataError,
    RegionError,
    NoValidOptionsError,

    # Integration Exceptions
    CurrencyConversionError,
    DataSourceError,
    CachingError,
    APIError,

    # System Exceptions
    QuotaExceededError,
    ComparisonTimeoutError,
)

__version__ = "0.1.0"

__all__ = [
    # Cloud Providers and Categories
    "CloudProvider",
    "OperatingSystem",
    "VMCategory",
    "PricingModel",
    "BillingTerm",

    # Core Models
    "VMSpecs",
    "VMRequirements",
    "VMInstance",
    "VMPricing",
    "VMCostBreakdown",
    "VMCostEstimate",

    # Comparison Models
    "ComparisonCriteria",
    "ComparisonResult",
    "PerformanceMetrics",
    "ComparisonRequest",
    "ComparisonResponse",

    # Base Exceptions
    "VMComparisonError",
    "ValidationError",
    "ConfigurationError",

    # Provider and Instance Exceptions
    "ProviderError",
    "PricingError",
    "InstanceNotFoundError",
    "RequirementsNotMetError",

    # Comparison Exceptions
    "ComparisonError",
    "PerformanceDataError",
    "RegionError",
    "NoValidOptionsError",

    # Integration Exceptions
    "CurrencyConversionError",
    "DataSourceError",
    "CachingError",
    "APIError",

    # System Exceptions
    "QuotaExceededError",
    "ComparisonTimeoutError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
