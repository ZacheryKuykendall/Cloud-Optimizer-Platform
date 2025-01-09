"""Custom exceptions for cloud cost normalization.

This module defines exceptions specific to cloud cost normalization operations,
including currency conversion, data validation, and provider-specific errors.
"""

from typing import Any, List, Optional


class CloudCostNormalizationError(Exception):
    """Base exception for all cloud cost normalization errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(CloudCostNormalizationError):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_value: Any = None):
        super().__init__(message)
        self.invalid_value = invalid_value


class CurrencyError(CloudCostNormalizationError):
    """Base class for currency-related errors."""
    pass


class InvalidCurrencyError(CurrencyError):
    """Raised when an invalid currency code is provided."""

    def __init__(self, message: str, currency_code: Optional[str] = None):
        super().__init__(message)
        self.currency_code = currency_code


class CurrencyConversionError(CurrencyError):
    """Raised when currency conversion fails."""

    def __init__(
        self,
        message: str,
        source_currency: Optional[str] = None,
        target_currency: Optional[str] = None,
        rate: Optional[float] = None
    ):
        super().__init__(message)
        self.source_currency = source_currency
        self.target_currency = target_currency
        self.rate = rate


class RateNotFoundError(CurrencyError):
    """Raised when an exchange rate is not available."""

    def __init__(
        self,
        message: str,
        source_currency: Optional[str] = None,
        target_currency: Optional[str] = None,
        date: Optional[str] = None
    ):
        super().__init__(message)
        self.source_currency = source_currency
        self.target_currency = target_currency
        self.date = date


class ProviderError(CloudCostNormalizationError):
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


class DataNormalizationError(CloudCostNormalizationError):
    """Raised when cost data normalization fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        resource_type: Optional[str] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_type = resource_type
        self.details = details or {}


class ResourceMappingError(CloudCostNormalizationError):
    """Raised when resource type mapping fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        provider_type: str,
        available_mappings: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.provider_type = provider_type
        self.available_mappings = available_mappings


class StorageError(CloudCostNormalizationError):
    """Raised when there are issues with cost data storage."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[dict] = None
    ):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}


class ConfigurationError(CloudCostNormalizationError):
    """Raised when there are issues with configuration."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ):
        super().__init__(message)
        self.config_key = config_key
        self.config_value = config_value


class CacheError(CloudCostNormalizationError):
    """Raised when there are issues with caching."""

    def __init__(
        self,
        message: str,
        cache_key: Optional[str] = None,
        operation: Optional[str] = None
    ):
        super().__init__(message)
        self.cache_key = cache_key
        self.operation = operation


class DateRangeError(ValidationError):
    """Raised when there are issues with date ranges."""

    def __init__(
        self,
        message: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        super().__init__(message)
        self.start_date = start_date
        self.end_date = end_date


class AggregationError(CloudCostNormalizationError):
    """Raised when cost data aggregation fails."""

    def __init__(
        self,
        message: str,
        group_by: Optional[List[str]] = None,
        time_period: Optional[str] = None
    ):
        super().__init__(message)
        self.group_by = group_by
        self.time_period = time_period
