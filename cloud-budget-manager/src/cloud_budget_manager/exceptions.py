"""Custom exceptions for cloud budget management.

This module defines exceptions specific to budget tracking, alerts,
and cost forecasting across different cloud providers.
"""

from typing import Any, Dict, List, Optional


class BudgetManagerError(Exception):
    """Base exception for all budget manager errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(BudgetManagerError):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_value: Any = None):
        super().__init__(message)
        self.invalid_value = invalid_value


class BudgetError(BudgetManagerError):
    """Base class for budget-related errors."""
    pass


class BudgetNotFoundError(BudgetError):
    """Raised when a budget cannot be found."""

    def __init__(
        self,
        message: str,
        budget_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.budget_id = budget_id
        self.details = details or {}


class BudgetAlreadyExistsError(BudgetError):
    """Raised when attempting to create a budget that already exists."""

    def __init__(
        self,
        message: str,
        budget_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.budget_id = budget_id
        self.details = details or {}


class BudgetUpdateError(BudgetError):
    """Raised when updating a budget fails."""

    def __init__(
        self,
        message: str,
        budget_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.budget_id = budget_id
        self.details = details or {}


class BudgetDeletionError(BudgetError):
    """Raised when deleting a budget fails."""

    def __init__(
        self,
        message: str,
        budget_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.budget_id = budget_id
        self.details = details or {}


class AlertError(BudgetManagerError):
    """Base class for alert-related errors."""
    pass


class AlertNotFoundError(AlertError):
    """Raised when an alert cannot be found."""

    def __init__(
        self,
        message: str,
        alert_id: str,
        budget_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.alert_id = alert_id
        self.budget_id = budget_id
        self.details = details or {}


class AlertUpdateError(AlertError):
    """Raised when updating an alert fails."""

    def __init__(
        self,
        message: str,
        alert_id: str,
        budget_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.alert_id = alert_id
        self.budget_id = budget_id
        self.details = details or {}


class NotificationError(BudgetManagerError):
    """Raised when sending alert notifications fails."""

    def __init__(
        self,
        message: str,
        alert_id: str,
        channels: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.alert_id = alert_id
        self.channels = channels
        self.details = details or {}


class ForecastError(BudgetManagerError):
    """Base class for forecast-related errors."""
    pass


class ForecastGenerationError(ForecastError):
    """Raised when generating a spending forecast fails."""

    def __init__(
        self,
        message: str,
        budget_id: str,
        period: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.budget_id = budget_id
        self.period = period
        self.details = details or {}


class InsufficientDataError(ForecastError):
    """Raised when there is insufficient data for forecasting."""

    def __init__(
        self,
        message: str,
        budget_id: str,
        required_points: int,
        available_points: int
    ):
        super().__init__(message)
        self.budget_id = budget_id
        self.required_points = required_points
        self.available_points = available_points


class ProviderError(BudgetManagerError):
    """Base class for cloud provider-related errors."""
    pass


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


class CostDataError(BudgetManagerError):
    """Base class for cost data-related errors."""
    pass


class CostDataFetchError(CostDataError):
    """Raised when fetching cost data fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        period: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.period = period
        self.details = details or {}


class CostDataParsingError(CostDataError):
    """Raised when parsing cost data fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        data_format: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.data_format = data_format
        self.details = details or {}


class QueryError(BudgetManagerError):
    """Base class for query-related errors."""
    pass


class InvalidQueryError(QueryError):
    """Raised when a budget query is invalid."""

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
    """Raised when a budget query times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: int,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
        self.details = details or {}


class CurrencyError(BudgetManagerError):
    """Base class for currency-related errors."""
    pass


class CurrencyConversionError(CurrencyError):
    """Raised when currency conversion fails."""

    def __init__(
        self,
        message: str,
        from_currency: str,
        to_currency: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.details = details or {}


class ExchangeRateError(CurrencyError):
    """Raised when fetching exchange rates fails."""

    def __init__(
        self,
        message: str,
        currency: str,
        provider: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.currency = currency
        self.provider = provider
        self.details = details or {}
