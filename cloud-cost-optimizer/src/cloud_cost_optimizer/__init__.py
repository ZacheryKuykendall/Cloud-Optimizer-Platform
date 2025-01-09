"""Cloud Cost Optimizer

A Python library for optimizing cloud costs across different services and providers.
This library provides functionality for analyzing resource usage patterns,
generating cost optimization recommendations, and implementing cost-saving measures.
"""

from cloud_cost_optimizer.models import (
    ResourceType,
    OptimizationType,
    UsagePattern,
    ResourceMetrics,
    CostMetrics,
    ResourceConfiguration,
    OptimizationRecommendation,
    ResourceUsageAnalysis,
    CloudResource,
    StorageOptimization,
    NetworkOptimization,
    ReservedCapacityRecommendation,
    OptimizationSummary,
    SchedulingPolicy,
    AutoScalingPolicy,
)
from cloud_cost_optimizer.exceptions import (
    CloudCostOptimizerError,
    ResourceError,
    ResourceNotFoundError,
    ResourceAccessError,
    MetricsError,
    OptimizationError,
    ValidationError,
    ProviderError,
    ConfigurationError,
    AnalysisError,
    RecommendationError,
    DataError,
    StorageOptimizationError,
    NetworkOptimizationError,
    SchedulingError,
    AutoScalingError,
)

__version__ = "0.1.0"

__all__ = [
    # Resource Types and Enums
    "ResourceType",
    "OptimizationType",
    "UsagePattern",

    # Core Models
    "ResourceMetrics",
    "CostMetrics",
    "ResourceConfiguration",
    "OptimizationRecommendation",
    "ResourceUsageAnalysis",
    "CloudResource",

    # Optimization Models
    "StorageOptimization",
    "NetworkOptimization",
    "ReservedCapacityRecommendation",
    "OptimizationSummary",
    "SchedulingPolicy",
    "AutoScalingPolicy",

    # Base Exceptions
    "CloudCostOptimizerError",
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceAccessError",
    "MetricsError",
    "OptimizationError",
    "ValidationError",
    "ProviderError",
    "ConfigurationError",
    "AnalysisError",
    "RecommendationError",
    "DataError",

    # Specific Optimization Exceptions
    "StorageOptimizationError",
    "NetworkOptimizationError",
    "SchedulingError",
    "AutoScalingError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
