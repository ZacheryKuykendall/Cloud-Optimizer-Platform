"""Cloud Resource Inventory.

A Python library for tracking and managing cloud resources across multiple cloud providers.
"""

from cloud_resource_inventory.exceptions import (
    GroupAlreadyExistsError,
    GroupNotFoundError,
    InvalidQueryError,
    ProviderAuthenticationError,
    ProviderAPIError,
    QueryTimeoutError,
    ResourceAccessError,
    ResourceAlreadyExistsError,
    ResourceDeletionError,
    ResourceInventoryError,
    ResourceNotFoundError,
    ResourceUpdateError,
    TagLimitExceededError,
    TagValidationError,
    UnsupportedProviderError,
    ValidationError,
)
from cloud_resource_inventory.inventory import ResourceInventoryManager
from cloud_resource_inventory.models import (
    CloudProvider,
    Resource,
    ResourceConfiguration,
    ResourceCost,
    ResourceCriticality,
    ResourceGroup,
    ResourceInventoryState,
    ResourceLifecycle,
    ResourceMetadata,
    ResourceMonitoring,
    ResourceQuery,
    ResourceStatus,
    ResourceSummary,
    ResourceTag,
    ResourceType,
)

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    # Main classes
    "ResourceInventoryManager",
    
    # Models
    "CloudProvider",
    "Resource",
    "ResourceConfiguration",
    "ResourceCost",
    "ResourceCriticality",
    "ResourceGroup",
    "ResourceInventoryState",
    "ResourceLifecycle",
    "ResourceMetadata",
    "ResourceMonitoring",
    "ResourceQuery",
    "ResourceStatus",
    "ResourceSummary",
    "ResourceTag",
    "ResourceType",
    
    # Exceptions
    "GroupAlreadyExistsError",
    "GroupNotFoundError",
    "InvalidQueryError",
    "ProviderAuthenticationError",
    "ProviderAPIError",
    "QueryTimeoutError",
    "ResourceAccessError",
    "ResourceAlreadyExistsError",
    "ResourceDeletionError",
    "ResourceInventoryError",
    "ResourceNotFoundError",
    "ResourceUpdateError",
    "TagLimitExceededError",
    "TagValidationError",
    "UnsupportedProviderError",
    "ValidationError",
]
