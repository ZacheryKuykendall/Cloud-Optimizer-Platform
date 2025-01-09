"""Custom exceptions for cloud resource inventory.

This module defines exceptions specific to resource tracking and management
across different cloud providers.
"""

from typing import Any, Dict, List, Optional


class ResourceInventoryError(Exception):
    """Base exception for all resource inventory errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(ResourceInventoryError):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_value: Any = None):
        super().__init__(message)
        self.invalid_value = invalid_value


class ResourceError(ResourceInventoryError):
    """Base class for resource-related errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a resource cannot be found."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.details = details or {}


class ResourceAlreadyExistsError(ResourceError):
    """Raised when attempting to create a resource that already exists."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.details = details or {}


class ResourceAccessError(ResourceError):
    """Raised when there are issues accessing resource data."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.details = details or {}


class ResourceUpdateError(ResourceError):
    """Raised when updating a resource fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.details = details or {}


class ResourceDeletionError(ResourceError):
    """Raised when deleting a resource fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.details = details or {}


class ResourceGroupError(ResourceInventoryError):
    """Base class for resource group-related errors."""
    pass


class GroupNotFoundError(ResourceGroupError):
    """Raised when a resource group cannot be found."""

    def __init__(
        self,
        message: str,
        group_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.group_id = group_id
        self.details = details or {}


class GroupAlreadyExistsError(ResourceGroupError):
    """Raised when attempting to create a group that already exists."""

    def __init__(
        self,
        message: str,
        group_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.group_id = group_id
        self.details = details or {}


class TagError(ResourceInventoryError):
    """Base class for tag-related errors."""
    pass


class TagValidationError(TagError):
    """Raised when tag validation fails."""

    def __init__(
        self,
        message: str,
        tag_key: str,
        tag_value: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.tag_key = tag_key
        self.tag_value = tag_value
        self.details = details or {}


class TagLimitExceededError(TagError):
    """Raised when tag limit is exceeded."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        current_count: int,
        max_count: int
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.current_count = current_count
        self.max_count = max_count


class ComplianceError(ResourceInventoryError):
    """Base class for compliance-related errors."""
    pass


class ComplianceCheckError(ComplianceError):
    """Raised when a compliance check fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        framework: str,
        violations: List[str]
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.framework = framework
        self.violations = violations


class BackupError(ResourceInventoryError):
    """Base class for backup-related errors."""
    pass


class BackupCreationError(BackupError):
    """Raised when creating a backup fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.details = details or {}


class BackupRestoreError(BackupError):
    """Raised when restoring from a backup fails."""

    def __init__(
        self,
        message: str,
        backup_id: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.backup_id = backup_id
        self.resource_id = resource_id
        self.details = details or {}


class MonitoringError(ResourceInventoryError):
    """Base class for monitoring-related errors."""
    pass


class MetricsCollectionError(MonitoringError):
    """Raised when collecting metrics fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        metrics: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.metrics = metrics
        self.details = details or {}


class AlertConfigurationError(MonitoringError):
    """Raised when configuring alerts fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        alert_config: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.alert_config = alert_config
        self.details = details or {}


class ProviderError(ResourceInventoryError):
    """Base class for cloud provider-related errors."""
    pass


class UnsupportedProviderError(ProviderError):
    """Raised when an unsupported cloud provider is specified."""

    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class ProviderAuthenticationError(ProviderError):
    """Raised when authentication with a cloud provider fails."""

    def __init__(self, message: str, provider: str):
        super().__init__(message)
        self.provider = provider


class ProviderAPIError(ProviderError):
    """Raised when a cloud provider API request fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        response: Optional[str] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.response = response


class QueryError(ResourceInventoryError):
    """Base class for query-related errors."""
    pass


class InvalidQueryError(QueryError):
    """Raised when a resource query is invalid."""

    def __init__(
        self,
        message: str,
        query_params: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.query_params = query_params
        self.details = details or {}


class QueryTimeoutError(QueryError):
    """Raised when a resource query times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: int,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
        self.details = details or {}
