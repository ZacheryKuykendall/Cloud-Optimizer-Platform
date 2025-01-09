"""Custom exceptions for GCP Cloud Billing client."""

from typing import Any, Dict, Optional


class GCPBillingError(Exception):
    """Base exception for GCP Cloud Billing client."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(GCPBillingError):
    """Raised when authentication with GCP fails."""

    def __init__(
        self, message: str = "Failed to authenticate with GCP", details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)


class ConfigurationError(GCPBillingError):
    """Raised when there's an issue with client configuration."""

    def __init__(
        self,
        message: str = "Invalid client configuration",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class ValidationError(GCPBillingError):
    """Raised when request parameters are invalid."""

    def __init__(
        self,
        message: str = "Invalid request parameters",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class APIError(GCPBillingError):
    """Raised when GCP Cloud Billing API returns an error."""

    def __init__(
        self,
        message: str = "GCP Cloud Billing API error",
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
            status_code: HTTP status code
        """
        super().__init__(message, details)
        self.status_code = status_code


class RateLimitError(APIError):
    """Raised when GCP Cloud Billing API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message, details, status_code=429)
        self.retry_after = retry_after


class DataNotFoundError(APIError):
    """Raised when requested billing data is not found."""

    def __init__(
        self,
        message: str = "Billing data not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details, status_code=404)


class InvalidBillingAccountError(ValidationError):
    """Raised when the billing account is invalid."""

    def __init__(
        self,
        message: str = "Invalid billing account",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class InvalidTimeframeError(ValidationError):
    """Raised when the timeframe is invalid."""

    def __init__(
        self,
        message: str = "Invalid timeframe",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class InvalidMetricError(ValidationError):
    """Raised when requested metric is invalid."""

    def __init__(
        self,
        message: str = "Invalid metric",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class InvalidFilterError(ValidationError):
    """Raised when billing filter is invalid."""

    def __init__(
        self,
        message: str = "Invalid billing filter",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class InvalidGroupingError(ValidationError):
    """Raised when grouping configuration is invalid."""

    def __init__(
        self,
        message: str = "Invalid grouping configuration",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class BudgetError(GCPBillingError):
    """Raised when there's an issue with budget operations."""

    def __init__(
        self,
        message: str = "Budget operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class ExportError(GCPBillingError):
    """Raised when there's an issue with billing data export."""

    def __init__(
        self,
        message: str = "Export operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class CacheError(GCPBillingError):
    """Raised when there's an issue with response caching."""

    def __init__(
        self,
        message: str = "Cache operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class RetryError(GCPBillingError):
    """Raised when all retry attempts fail."""

    def __init__(
        self,
        message: str = "All retry attempts failed",
        details: Optional[Dict[str, Any]] = None,
        attempts: int = 0,
        last_exception: Optional[Exception] = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
            attempts: Number of retry attempts made
            last_exception: Last exception that caused the retry failure
        """
        super().__init__(message, details)
        self.attempts = attempts
        self.last_exception = last_exception


class CredentialsError(GCPBillingError):
    """Raised when there's an issue with GCP credentials."""

    def __init__(
        self,
        message: str = "Invalid GCP credentials",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class ProjectError(GCPBillingError):
    """Raised when there's an issue with GCP project."""

    def __init__(
        self,
        message: str = "Invalid GCP project",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class ServiceError(GCPBillingError):
    """Raised when there's an issue with GCP service."""

    def __init__(
        self,
        message: str = "Invalid GCP service",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class BigQueryError(GCPBillingError):
    """Raised when there's an issue with BigQuery operations."""

    def __init__(
        self,
        message: str = "BigQuery operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class CloudStorageError(GCPBillingError):
    """Raised when there's an issue with Cloud Storage operations."""

    def __init__(
        self,
        message: str = "Cloud Storage operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class PubSubError(GCPBillingError):
    """Raised when there's an issue with Pub/Sub operations."""

    def __init__(
        self,
        message: str = "Pub/Sub operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
