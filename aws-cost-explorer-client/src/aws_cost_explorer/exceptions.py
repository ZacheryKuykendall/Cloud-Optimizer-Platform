"""Custom exceptions for AWS Cost Explorer client."""

from typing import Any, Dict, Optional


class AWSCostExplorerError(Exception):
    """Base exception for AWS Cost Explorer client."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(AWSCostExplorerError):
    """Raised when authentication with AWS fails."""

    def __init__(
        self, message: str = "Failed to authenticate with AWS", details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)


class ConfigurationError(AWSCostExplorerError):
    """Raised when there's an issue with client configuration."""

    def __init__(
        self,
        message: str = "Invalid client configuration",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class ValidationError(AWSCostExplorerError):
    """Raised when request parameters are invalid."""

    def __init__(
        self,
        message: str = "Invalid request parameters",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class APIError(AWSCostExplorerError):
    """Raised when AWS Cost Explorer API returns an error."""

    def __init__(
        self,
        message: str = "AWS Cost Explorer API error",
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
    """Raised when AWS Cost Explorer API rate limit is exceeded."""

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


class ServiceQuotaExceededError(APIError):
    """Raised when AWS service quota is exceeded."""

    def __init__(
        self,
        message: str = "Service quota exceeded",
        details: Optional[Dict[str, Any]] = None,
        quota_name: Optional[str] = None,
        quota_value: Optional[float] = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            details: Additional error details
            quota_name: Name of the exceeded quota
            quota_value: Value of the exceeded quota
        """
        super().__init__(message, details, status_code=402)
        self.quota_name = quota_name
        self.quota_value = quota_value


class InvalidDateRangeError(ValidationError):
    """Raised when date range is invalid."""

    def __init__(
        self,
        message: str = "Invalid date range",
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


class CacheError(AWSCostExplorerError):
    """Raised when there's an issue with response caching."""

    def __init__(
        self,
        message: str = "Cache operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class RetryError(AWSCostExplorerError):
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


class SessionError(AWSCostExplorerError):
    """Raised when there's an issue with AWS session management."""

    def __init__(
        self,
        message: str = "Session error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class CredentialsError(AWSCostExplorerError):
    """Raised when there's an issue with AWS credentials."""

    def __init__(
        self,
        message: str = "Invalid AWS credentials",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)


class RegionError(AWSCostExplorerError):
    """Raised when there's an issue with AWS region configuration."""

    def __init__(
        self,
        message: str = "Invalid AWS region",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
