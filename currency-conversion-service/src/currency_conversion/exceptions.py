"""Custom exceptions for Currency Conversion Service.

This module defines exceptions specific to currency conversion operations,
including exchange rate errors and validation issues.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID


class CurrencyConversionError(Exception):
    """Base exception for all currency conversion errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(CurrencyConversionError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(CurrencyConversionError):
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


class RateProviderError(CurrencyConversionError):
    """Raised when there are issues with rate providers."""

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.response_body = response_body or {}


class RateLimitError(RateProviderError):
    """Raised when hitting rate provider API limits."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: Optional[int] = None
    ):
        super().__init__(message, provider)
        self.retry_after = retry_after


class UnsupportedCurrencyError(CurrencyConversionError):
    """Raised when a currency is not supported."""

    def __init__(
        self,
        message: str,
        currency: str,
        provider: Optional[str] = None
    ):
        super().__init__(message)
        self.currency = currency
        self.provider = provider


class NoExchangeRateError(CurrencyConversionError):
    """Raised when no exchange rate is available."""

    def __init__(
        self,
        message: str,
        source_currency: str,
        target_currency: str,
        reference_date: Optional[date] = None
    ):
        super().__init__(message)
        self.source_currency = source_currency
        self.target_currency = target_currency
        self.reference_date = reference_date


class StaleRateError(CurrencyConversionError):
    """Raised when exchange rate is too old."""

    def __init__(
        self,
        message: str,
        rate_timestamp: date,
        max_age_hours: int
    ):
        super().__init__(message)
        self.rate_timestamp = rate_timestamp
        self.max_age_hours = max_age_hours


class CacheError(CurrencyConversionError):
    """Raised when there are caching issues."""

    def __init__(
        self,
        message: str,
        cache_type: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.cache_type = cache_type
        self.operation = operation
        self.details = details or {}


class BatchConversionError(CurrencyConversionError):
    """Raised when there are issues with batch conversions."""

    def __init__(
        self,
        message: str,
        batch_id: UUID,
        failed_items: List[Dict[str, Any]],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.batch_id = batch_id
        self.failed_items = failed_items
        self.details = details or {}


class AlertConfigurationError(CurrencyConversionError):
    """Raised when there are issues with alert configuration."""

    def __init__(
        self,
        message: str,
        alert_id: Optional[UUID] = None,
        condition: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.alert_id = alert_id
        self.condition = condition
        self.details = details or {}


class DatabaseError(CurrencyConversionError):
    """Raised when there are database issues."""

    def __init__(
        self,
        message: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}


class MetricsError(CurrencyConversionError):
    """Raised when there are issues with metrics collection."""

    def __init__(
        self,
        message: str,
        metric_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.metric_type = metric_type
        self.details = details or {}


class ProviderSyncError(CurrencyConversionError):
    """Raised when there are issues syncing with rate providers."""

    def __init__(
        self,
        message: str,
        provider: str,
        last_sync: Optional[date] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.last_sync = last_sync
        self.details = details or {}


class InvalidOperationError(CurrencyConversionError):
    """Raised when attempting an invalid operation."""

    def __init__(
        self,
        message: str,
        operation: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.operation = operation
        self.reason = reason
        self.details = details or {}
