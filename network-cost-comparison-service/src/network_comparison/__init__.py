"""Network Cost Comparison Service

A service for comparing network costs across different cloud providers,
providing detailed cost analysis, performance metrics, and optimization recommendations.
"""

from network_comparison.models import (
    # Cloud Providers and Network Types
    CloudProvider,
    NetworkServiceType,
    NetworkTier,
    LoadBalancerType,
    ConnectivityType,
    AvailabilityLevel,

    # Core Models
    NetworkFeatures,
    PerformanceSpecs,
    NetworkRequirements,
    NetworkService,
    PricingComponent,
    NetworkPricing,
    CostBreakdown,
    NetworkCostEstimate,

    # Comparison Models
    ComparisonCriteria,
    ComparisonResult,
    PerformanceMetrics,
    ComparisonRequest,
    ComparisonResponse,
)

from network_comparison.exceptions import (
    # Base Exceptions
    NetworkComparisonError,
    ValidationError,
    ConfigurationError,

    # Provider and Service Exceptions
    ProviderError,
    NetworkServiceError,
    PricingError,
    NetworkRequirementsError,

    # Network-Specific Exceptions
    BandwidthError,
    LatencyError,
    NetworkPerformanceError,
    NetworkFeatureError,
    NetworkAvailabilityError,

    # Comparison Exceptions
    ComparisonError,
    PerformanceDataError,
    RegionError,
    NoValidOptionsError,

    # Analysis Exceptions
    ComplianceError,
    CostAnalysisError,

    # System Exceptions
    DataSourceError,
    ComparisonTimeoutError,
)

__version__ = "0.1.0"

__all__ = [
    # Cloud Providers and Network Types
    "CloudProvider",
    "NetworkServiceType",
    "NetworkTier",
    "LoadBalancerType",
    "ConnectivityType",
    "AvailabilityLevel",

    # Core Models
    "NetworkFeatures",
    "PerformanceSpecs",
    "NetworkRequirements",
    "NetworkService",
    "PricingComponent",
    "NetworkPricing",
    "CostBreakdown",
    "NetworkCostEstimate",

    # Comparison Models
    "ComparisonCriteria",
    "ComparisonResult",
    "PerformanceMetrics",
    "ComparisonRequest",
    "ComparisonResponse",

    # Base Exceptions
    "NetworkComparisonError",
    "ValidationError",
    "ConfigurationError",

    # Provider and Service Exceptions
    "ProviderError",
    "NetworkServiceError",
    "PricingError",
    "NetworkRequirementsError",

    # Network-Specific Exceptions
    "BandwidthError",
    "LatencyError",
    "NetworkPerformanceError",
    "NetworkFeatureError",
    "NetworkAvailabilityError",

    # Comparison Exceptions
    "ComparisonError",
    "PerformanceDataError",
    "RegionError",
    "NoValidOptionsError",

    # Analysis Exceptions
    "ComplianceError",
    "CostAnalysisError",

    # System Exceptions
    "DataSourceError",
    "ComparisonTimeoutError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
