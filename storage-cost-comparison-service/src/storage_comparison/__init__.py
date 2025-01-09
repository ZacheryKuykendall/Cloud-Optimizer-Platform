"""Storage Cost Comparison Service

A service for comparing storage costs across different cloud providers,
providing detailed cost analysis, performance metrics, and optimization recommendations.
"""

from storage_comparison.models import (
    # Cloud Providers and Storage Types
    CloudProvider,
    StorageType,
    StorageTier,
    AccessPattern,
    DataRedundancy,

    # Core Models
    StorageFeatures,
    PerformanceSpecs,
    StorageRequirements,
    StorageService,
    PricingComponent,
    StoragePricing,
    CostBreakdown,
    StorageCostEstimate,

    # Comparison Models
    ComparisonCriteria,
    ComparisonResult,
    PerformanceMetrics,
    ComparisonRequest,
    ComparisonResponse,
)

from storage_comparison.exceptions import (
    # Base Exceptions
    StorageComparisonError,
    ValidationError,
    ConfigurationError,

    # Provider and Service Exceptions
    ProviderError,
    StorageServiceError,
    PricingError,
    StorageRequirementsError,

    # Comparison Exceptions
    ComparisonError,
    PerformanceDataError,
    RegionError,
    NoValidOptionsError,

    # Storage-Specific Exceptions
    StorageTypeError,
    CapacityError,
    DataRedundancyError,
    FeatureCompatibilityError,

    # Analysis Exceptions
    ComplianceError,
    PerformanceRequirementError,
    CostAnalysisError,

    # System Exceptions
    DataSourceError,
    ComparisonTimeoutError,
)

__version__ = "0.1.0"

__all__ = [
    # Cloud Providers and Storage Types
    "CloudProvider",
    "StorageType",
    "StorageTier",
    "AccessPattern",
    "DataRedundancy",

    # Core Models
    "StorageFeatures",
    "PerformanceSpecs",
    "StorageRequirements",
    "StorageService",
    "PricingComponent",
    "StoragePricing",
    "CostBreakdown",
    "StorageCostEstimate",

    # Comparison Models
    "ComparisonCriteria",
    "ComparisonResult",
    "PerformanceMetrics",
    "ComparisonRequest",
    "ComparisonResponse",

    # Base Exceptions
    "StorageComparisonError",
    "ValidationError",
    "ConfigurationError",

    # Provider and Service Exceptions
    "ProviderError",
    "StorageServiceError",
    "PricingError",
    "StorageRequirementsError",

    # Comparison Exceptions
    "ComparisonError",
    "PerformanceDataError",
    "RegionError",
    "NoValidOptionsError",

    # Storage-Specific Exceptions
    "StorageTypeError",
    "CapacityError",
    "DataRedundancyError",
    "FeatureCompatibilityError",

    # Analysis Exceptions
    "ComplianceError",
    "PerformanceRequirementError",
    "CostAnalysisError",

    # System Exceptions
    "DataSourceError",
    "ComparisonTimeoutError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
