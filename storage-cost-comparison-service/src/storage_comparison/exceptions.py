"""Custom exceptions for storage cost comparison service.

This module defines exceptions specific to comparing storage costs
across different cloud providers.
"""

from typing import Any, Dict, List, Optional


class StorageComparisonError(Exception):
    """Base exception for all storage comparison errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ValidationError(StorageComparisonError):
    """Raised when storage requirements validation fails."""

    def __init__(
        self,
        message: str,
        field: str,
        value: Any,
        constraints: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "field": field,
                "value": value,
                "constraints": constraints or {}
            }
        )
        self.field = field
        self.value = value
        self.constraints = constraints or {}


class ProviderError(StorageComparisonError):
    """Base class for cloud provider-specific errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "error_code": error_code,
                **(details or {})
            }
        )
        self.provider = provider
        self.error_code = error_code


class PricingError(StorageComparisonError):
    """Raised when there's an error retrieving or calculating pricing."""

    def __init__(
        self,
        message: str,
        provider: str,
        region: str,
        storage_type: Optional[str] = None,
        storage_class: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "region": region,
                "storage_type": storage_type,
                "storage_class": storage_class,
                **(details or {})
            }
        )
        self.provider = provider
        self.region = region
        self.storage_type = storage_type
        self.storage_class = storage_class


class NoMatchingOptionsError(StorageComparisonError):
    """Raised when no storage options match the specified requirements."""

    def __init__(
        self,
        message: str,
        requirements: Dict[str, Any],
        providers: List[str],
        regions: List[str]
    ):
        super().__init__(
            message,
            details={
                "requirements": requirements,
                "providers": providers,
                "regions": regions
            }
        )
        self.requirements = requirements
        self.providers = providers
        self.regions = regions


class StorageClassNotSupportedError(StorageComparisonError):
    """Raised when a storage class is not supported in a region."""

    def __init__(
        self,
        message: str,
        provider: str,
        storage_class: str,
        region: str,
        supported_classes: List[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "storage_class": storage_class,
                "region": region,
                "supported_classes": supported_classes
            }
        )
        self.provider = provider
        self.storage_class = storage_class
        self.region = region
        self.supported_classes = supported_classes


class PerformanceTierNotSupportedError(StorageComparisonError):
    """Raised when a performance tier is not supported."""

    def __init__(
        self,
        message: str,
        provider: str,
        performance_tier: str,
        storage_type: str,
        supported_tiers: List[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "performance_tier": performance_tier,
                "storage_type": storage_type,
                "supported_tiers": supported_tiers
            }
        )
        self.provider = provider
        self.performance_tier = performance_tier
        self.storage_type = storage_type
        self.supported_tiers = supported_tiers


class ReplicationNotSupportedError(StorageComparisonError):
    """Raised when a replication type is not supported."""

    def __init__(
        self,
        message: str,
        provider: str,
        replication_type: str,
        storage_class: str,
        supported_types: List[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "replication_type": replication_type,
                "storage_class": storage_class,
                "supported_types": supported_types
            }
        )
        self.provider = provider
        self.replication_type = replication_type
        self.storage_class = storage_class
        self.supported_types = supported_types


class CapacityError(StorageComparisonError):
    """Raised when capacity requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        storage_type: str,
        requested_gb: float,
        min_gb: float,
        max_gb: Optional[float] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "storage_type": storage_type,
                "requested_gb": requested_gb,
                "min_gb": min_gb,
                "max_gb": max_gb
            }
        )
        self.provider = provider
        self.storage_type = storage_type
        self.requested_gb = requested_gb
        self.min_gb = min_gb
        self.max_gb = max_gb


class PerformanceError(StorageComparisonError):
    """Raised when performance requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        storage_type: str,
        metric: str,
        requested_value: float,
        available_value: float
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "storage_type": storage_type,
                "metric": metric,
                "requested_value": requested_value,
                "available_value": available_value
            }
        )
        self.provider = provider
        self.storage_type = storage_type
        self.metric = metric
        self.requested_value = requested_value
        self.available_value = available_value


class FeatureNotSupportedError(StorageComparisonError):
    """Raised when a required feature is not supported."""

    def __init__(
        self,
        message: str,
        feature: str,
        provider: str,
        storage_type: str,
        storage_class: Optional[str] = None
    ):
        super().__init__(
            message,
            details={
                "feature": feature,
                "provider": provider,
                "storage_type": storage_type,
                "storage_class": storage_class
            }
        )
        self.feature = feature
        self.provider = provider
        self.storage_type = storage_type
        self.storage_class = storage_class


class ComparisonTimeoutError(StorageComparisonError):
    """Raised when a comparison operation times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: int,
        partial_results: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "timeout_seconds": timeout_seconds,
                "partial_results": partial_results
            }
        )
        self.timeout_seconds = timeout_seconds
        self.partial_results = partial_results


class FilterValidationError(StorageComparisonError):
    """Raised when comparison filters are invalid."""

    def __init__(
        self,
        message: str,
        invalid_filters: Dict[str, Any],
        valid_options: Optional[Dict[str, List[Any]]] = None
    ):
        super().__init__(
            message,
            details={
                "invalid_filters": invalid_filters,
                "valid_options": valid_options
            }
        )
        self.invalid_filters = invalid_filters
        self.valid_options = valid_options


class RateLimitError(StorageComparisonError):
    """Raised when rate limits are exceeded for pricing APIs."""

    def __init__(
        self,
        message: str,
        provider: str,
        limit: Optional[int] = None,
        reset_time: Optional[str] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "limit": limit,
                "reset_time": reset_time
            }
        )
        self.provider = provider
        self.limit = limit
        self.reset_time = reset_time
