"""Custom exceptions for network cost comparison service.

This module defines exceptions specific to comparing network costs
across different cloud providers.
"""

from typing import Any, Dict, List, Optional


class NetworkComparisonError(Exception):
    """Base exception for all network comparison errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ValidationError(NetworkComparisonError):
    """Raised when network requirements validation fails."""

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


class ProviderError(NetworkComparisonError):
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


class PricingError(NetworkComparisonError):
    """Raised when there's an error retrieving or calculating pricing."""

    def __init__(
        self,
        message: str,
        provider: str,
        region: str,
        service_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "region": region,
                "service_type": service_type,
                **(details or {})
            }
        )
        self.provider = provider
        self.region = region
        self.service_type = service_type


class NoMatchingOptionsError(NetworkComparisonError):
    """Raised when no network options match the specified requirements."""

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


class ServiceTypeNotSupportedError(NetworkComparisonError):
    """Raised when a network service type is not supported."""

    def __init__(
        self,
        message: str,
        provider: str,
        service_type: str,
        region: str,
        supported_types: List[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "service_type": service_type,
                "region": region,
                "supported_types": supported_types
            }
        )
        self.provider = provider
        self.service_type = service_type
        self.region = region
        self.supported_types = supported_types


class BandwidthError(NetworkComparisonError):
    """Raised when bandwidth requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        service_type: str,
        requested_gbps: float,
        min_gbps: float,
        max_gbps: Optional[float] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "service_type": service_type,
                "requested_gbps": requested_gbps,
                "min_gbps": min_gbps,
                "max_gbps": max_gbps
            }
        )
        self.provider = provider
        self.service_type = service_type
        self.requested_gbps = requested_gbps
        self.min_gbps = min_gbps
        self.max_gbps = max_gbps


class ThroughputError(NetworkComparisonError):
    """Raised when throughput requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        service_type: str,
        metric: str,
        requested_value: float,
        available_value: float
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "service_type": service_type,
                "metric": metric,
                "requested_value": requested_value,
                "available_value": available_value
            }
        )
        self.provider = provider
        self.service_type = service_type
        self.metric = metric
        self.requested_value = requested_value
        self.available_value = available_value


class FeatureNotSupportedError(NetworkComparisonError):
    """Raised when a required feature is not supported."""

    def __init__(
        self,
        message: str,
        feature: str,
        provider: str,
        service_type: str,
        region: str
    ):
        super().__init__(
            message,
            details={
                "feature": feature,
                "provider": provider,
                "service_type": service_type,
                "region": region
            }
        )
        self.feature = feature
        self.provider = provider
        self.service_type = service_type
        self.region = region


class ComparisonTimeoutError(NetworkComparisonError):
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


class FilterValidationError(NetworkComparisonError):
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


class RateLimitError(NetworkComparisonError):
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


class ServiceConfigurationError(NetworkComparisonError):
    """Raised when service configuration is invalid."""

    def __init__(
        self,
        message: str,
        provider: str,
        service_type: str,
        config_key: str,
        config_value: Any,
        valid_values: Optional[List[Any]] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "service_type": service_type,
                "config_key": config_key,
                "config_value": config_value,
                "valid_values": valid_values
            }
        )
        self.provider = provider
        self.service_type = service_type
        self.config_key = config_key
        self.config_value = config_value
        self.valid_values = valid_values


class NetworkAvailabilityError(NetworkComparisonError):
    """Raised when network service is not available in a region."""

    def __init__(
        self,
        message: str,
        provider: str,
        service_type: str,
        region: str,
        available_regions: List[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "service_type": service_type,
                "region": region,
                "available_regions": available_regions
            }
        )
        self.provider = provider
        self.service_type = service_type
        self.region = region
        self.available_regions = available_regions


class CrossRegionError(NetworkComparisonError):
    """Raised when cross-region requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        service_type: str,
        source_region: str,
        target_region: str,
        supported_pairs: Optional[List[Dict[str, str]]] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "service_type": service_type,
                "source_region": source_region,
                "target_region": target_region,
                "supported_pairs": supported_pairs
            }
        )
        self.provider = provider
        self.service_type = service_type
        self.source_region = source_region
        self.target_region = target_region
        self.supported_pairs = supported_pairs
