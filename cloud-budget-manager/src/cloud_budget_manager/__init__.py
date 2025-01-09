"""Cloud Budget Manager.

A Python library for managing cloud budgets, spending alerts, and cost forecasting
across multiple cloud providers.
"""

from cloud_budget_manager.exceptions import (
    AlertNotFoundError,
    AlertUpdateError,
    BudgetAlreadyExistsError,
    BudgetDeletionError,
    BudgetNotFoundError,
    BudgetUpdateError,
    CostDataFetchError,
    CurrencyConversionError,
    ForecastGenerationError,
    InsufficientDataError,
    InvalidQueryError,
    NotificationError,
    ProviderAPIError,
    ProviderAuthenticationError,
    ValidationError,
)
from cloud_budget_manager.manager import BudgetManager
from cloud_budget_manager.models import (
    AlertSeverity,
    AlertStatus,
    Budget,
    BudgetAdjustmentRecommendation,
    BudgetFilter,
    BudgetPeriod,
    BudgetQuery,
    BudgetState,
    BudgetSummary,
    CategorySpending,
    CloudProvider,
    ForecastAccuracy,
    ProviderSpending,
    SpendingAlert,
    SpendingForecast,
    SpendingMetrics,
    SpendingTrend,
)

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    # Main classes
    "BudgetManager",
    
    # Models
    "AlertSeverity",
    "AlertStatus",
    "Budget",
    "BudgetAdjustmentRecommendation",
    "BudgetFilter",
    "BudgetPeriod",
    "BudgetQuery",
    "BudgetState",
    "BudgetSummary",
    "CategorySpending",
    "CloudProvider",
    "ForecastAccuracy",
    "ProviderSpending",
    "SpendingAlert",
    "SpendingForecast",
    "SpendingMetrics",
    "SpendingTrend",
    
    # Exceptions
    "AlertNotFoundError",
    "AlertUpdateError",
    "BudgetAlreadyExistsError",
    "BudgetDeletionError",
    "BudgetNotFoundError",
    "BudgetUpdateError",
    "CostDataFetchError",
    "CurrencyConversionError",
    "ForecastGenerationError",
    "InsufficientDataError",
    "InvalidQueryError",
    "NotificationError",
    "ProviderAPIError",
    "ProviderAuthenticationError",
    "ValidationError",
]
