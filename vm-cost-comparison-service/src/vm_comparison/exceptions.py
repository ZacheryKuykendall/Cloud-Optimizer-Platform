"""Custom exceptions for VM cost comparison service.

This module defines exceptions specific to comparing virtual machine costs
across different cloud providers.
"""

from typing import Any, Dict, List, Optional


class VmComparisonError(Exception):
    """Base exception for all VM comparison errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ValidationError(VmComparisonError):
    """Raised when VM requirements validation fails."""

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


class ProviderError(VmComparisonError):
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


class PricingError(VmComparisonError):
    """Raised when there's an error retrieving or calculating pricing."""

    def __init__(
        self,
        message: str,
        provider: str,
        region: str,
        instance_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "region": region,
                "instance_type": instance_type,
                **(details or {})
            }
        )
        self.provider = provider
        self.region = region
        self.instance_type = instance_type


class NoMatchingInstancesError(VmComparisonError):
    """Raised when no instances match the specified requirements."""

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


class RegionNotSupportedError(VmComparisonError):
    """Raised when a specified region is not supported."""

    def __init__(
        self,
        message: str,
        provider: str,
        region: str,
        supported_regions: List[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "region": region,
                "supported_regions": supported_regions
            }
        )
        self.provider = provider
        self.region = region
        self.supported_regions = supported_regions


class FeatureNotSupportedError(VmComparisonError):
    """Raised when a required feature is not supported."""

    def __init__(
        self,
        message: str,
        feature: str,
        provider: str,
        instance_type: Optional[str] = None
    ):
        super().__init__(
            message,
            details={
                "feature": feature,
                "provider": provider,
                "instance_type": instance_type
            }
        )
        self.feature = feature
        self.provider = provider
        self.instance_type = instance_type


class CertificationNotSupportedError(VmComparisonError):
    """Raised when a required certification is not supported."""

    def __init__(
        self,
        message: str,
        certification: str,
        provider: str,
        region: Optional[str] = None
    ):
        super().__init__(
            message,
            details={
                "certification": certification,
                "provider": provider,
                "region": region
            }
        )
        self.certification = certification
        self.provider = provider
        self.region = region


class CacheError(VmComparisonError):
    """Raised when there's an error with the pricing cache."""

    def __init__(
        self,
        message: str,
        operation: str,
        cache_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "operation": operation,
                "cache_key": cache_key,
                **(details or {})
            }
        )
        self.operation = operation
        self.cache_key = cache_key


class ComparisonTimeoutError(VmComparisonError):
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


class FilterValidationError(VmComparisonError):
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


class DataSourceError(VmComparisonError):
    """Raised when there's an error with a pricing data source."""

    def __init__(
        self,
        message: str,
        source: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "source": source,
                "operation": operation,
                **(details or {})
            }
        )
        self.source = source
        self.operation = operation


class RateLimitError(VmComparisonError):
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
