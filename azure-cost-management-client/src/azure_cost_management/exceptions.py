"""Custom exceptions for Azure Cost Management client."""

from typing import Any, Dict, Optional


class AzureCostManagementError(Exception):
    """Base exception for Azure Cost Management client."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(AzureCostManagementError):
    """Raised when authentication with Azure fails."""

    def __init__(
        self, message: str = "Failed to authenticate with Azure", details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)


class ConfigurationError(AzureCostManagementError):
    """Raised when there's an issue with client configuration."""

    def __init__(
        self,
        message: str = "Invalid client configuration",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class ValidationError(AzureCostManagementError):
    """Raised when request parameters are invalid."""

    def __init__(
        self,
        message: str = "Invalid request parameters",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class APIError(AzureCostManagementError):
    """Raised when Azure Cost Management API returns an error."""

    def __init__(
        self,
        message: str = "Azure Cost Management API error",
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
    """Raised when Azure Cost Management API rate limit is exceeded."""

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
    """Raised when requested cost data is not found."""

    def __init__(
        self,
        message: str = "Cost data not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details, status_code=404)


class InvalidScopeError(ValidationError):
    """Raised when the scope is invalid."""

    def __init__(
        self,
        message: str = "Invalid scope",
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
    """Raised when cost filter is invalid."""

    def __init__(
        self,
        message: str = "Invalid cost filter",
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


class BudgetError(AzureCostManagementError):
    """Raised when there's an issue with budget operations."""

    def __init__(
        self,
        message: str = "Budget operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class CacheError(AzureCostManagementError):
    """Raised when there's an issue with response caching."""

    def __init__(
        self,
        message: str = "Cache operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class RetryError(AzureCostManagementError):
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


class CredentialsError(AzureCostManagementError):
    """Raised when there's an issue with Azure credentials."""

    def __init__(
        self,
        message: str = "Invalid Azure credentials",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class SubscriptionError(AzureCostManagementError):
    """Raised when there's an issue with Azure subscription."""

    def __init__(
        self,
        message: str = "Invalid Azure subscription",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class ResourceGroupError(AzureCostManagementError):
    """Raised when there's an issue with Azure resource group."""

    def __init__(
        self,
        message: str = "Invalid Azure resource group",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
