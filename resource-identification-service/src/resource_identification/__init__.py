"""Resource Identification Service

A service for identifying and classifying cloud resources across different providers.
Supports resource scanning, dependency analysis, and automatic classification.
"""

from resource_identification.models import (
    CloudProvider,
    ResourceType,
    ResourceStatus,
    ResourceTier,
    ResourceClassification,
    ResourceDependencyType,
    ResourceMetadata,
    ResourceDependency,
    ResourceUsage,
    ResourceConfiguration,
    CloudResource,
    ResourceScanConfig,
    ResourceScanResult,
    ResourceQuery,
    ResourceClassificationRule,
    ResourceDependencyGraph,
)
from resource_identification.exceptions import (
    ResourceIdentificationError,
    ValidationError,
    ConfigurationError,
    ProviderError,
    AuthenticationError,
    ResourceScanError,
    ResourceNotFoundError,
    DependencyError,
    ClassificationError,
    GraphAnalysisError,
    RateLimitError,
    ResourceAccessError,
    MetricsError,
    ConcurrencyError,
    TimeoutError,
)

__version__ = "0.1.0"

__all__ = [
    # Cloud Providers and Resource Types
    "CloudProvider",
    "ResourceType",
    "ResourceStatus",
    "ResourceTier",
    "ResourceClassification",
    "ResourceDependencyType",

    # Core Models
    "ResourceMetadata",
    "ResourceDependency",
    "ResourceUsage",
    "ResourceConfiguration",
    "CloudResource",

    # Scanning and Analysis
    "ResourceScanConfig",
    "ResourceScanResult",
    "ResourceQuery",
    "ResourceClassificationRule",
    "ResourceDependencyGraph",

    # Base Exceptions
    "ResourceIdentificationError",
    "ValidationError",
    "ConfigurationError",

    # Provider Exceptions
    "ProviderError",
    "AuthenticationError",
    "RateLimitError",

    # Resource Operation Exceptions
    "ResourceScanError",
    "ResourceNotFoundError",
    "DependencyError",
    "ClassificationError",
    "GraphAnalysisError",

    # System Exceptions
    "ResourceAccessError",
    "MetricsError",
    "ConcurrencyError",
    "TimeoutError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
