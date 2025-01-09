"""Custom exceptions for Resource Identification Service.

This module defines exceptions specific to resource identification operations,
including scanning, classification, and dependency analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


class ResourceIdentificationError(Exception):
    """Base exception for all resource identification errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(ResourceIdentificationError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(ResourceIdentificationError):
    """Raised when there are configuration issues."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ):
        super().__init__(message)
        self.config_key = config_key
        self.config_value = config_value


class ProviderError(ResourceIdentificationError):
    """Raised when there are issues with cloud providers."""

    def __init__(
        self,
        message: str,
        provider: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.details = details or {}


class AuthenticationError(ProviderError):
    """Raised when there are authentication issues with cloud providers."""

    def __init__(
        self,
        message: str,
        provider: str,
        credentials: Optional[Dict[str, str]] = None
    ):
        super().__init__(message, provider, "authenticate")
        self.credentials = credentials


class ResourceScanError(ResourceIdentificationError):
    """Raised when there are issues with resource scanning."""

    def __init__(
        self,
        message: str,
        scan_id: UUID,
        provider: str,
        region: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.scan_id = scan_id
        self.provider = provider
        self.region = region
        self.details = details or {}


class ResourceNotFoundError(ResourceIdentificationError):
    """Raised when a resource cannot be found."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        resource_type: Optional[str] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.resource_type = resource_type


class DependencyError(ResourceIdentificationError):
    """Raised when there are issues with resource dependencies."""

    def __init__(
        self,
        message: str,
        source_id: str,
        target_id: str,
        dependency_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.source_id = source_id
        self.target_id = target_id
        self.dependency_type = dependency_type
        self.details = details or {}


class ClassificationError(ResourceIdentificationError):
    """Raised when there are issues with resource classification."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        rule_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.rule_id = rule_id
        self.details = details or {}


class GraphAnalysisError(ResourceIdentificationError):
    """Raised when there are issues with dependency graph analysis."""

    def __init__(
        self,
        message: str,
        graph_id: UUID,
        analysis_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.graph_id = graph_id
        self.analysis_type = analysis_type
        self.details = details or {}


class RateLimitError(ProviderError):
    """Raised when hitting provider API rate limits."""

    def __init__(
        self,
        message: str,
        provider: str,
        limit: int,
        reset_time: Optional[datetime] = None
    ):
        super().__init__(message, provider, "rate_limit")
        self.limit = limit
        self.reset_time = reset_time


class ResourceAccessError(ResourceIdentificationError):
    """Raised when there are permission issues accessing resources."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        required_permissions: List[str],
        provider: str
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.required_permissions = required_permissions
        self.provider = provider


class MetricsError(ResourceIdentificationError):
    """Raised when there are issues collecting resource metrics."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        metric_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.metric_type = metric_type
        self.details = details or {}


class ConcurrencyError(ResourceIdentificationError):
    """Raised when there are issues with parallel scanning operations."""

    def __init__(
        self,
        message: str,
        operation: str,
        max_concurrent: int,
        current_concurrent: int
    ):
        super().__init__(message)
        self.operation = operation
        self.max_concurrent = max_concurrent
        self.current_concurrent = current_concurrent


class TimeoutError(ResourceIdentificationError):
    """Raised when operations exceed their time limit."""

    def __init__(
        self,
        message: str,
        operation: str,
        timeout_seconds: int,
        elapsed_seconds: float
    ):
        super().__init__(message)
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.elapsed_seconds = elapsed_seconds
