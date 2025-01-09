"""Custom exceptions for cloud cost optimization.

This module defines exceptions specific to cost optimization operations
across different cloud providers.
"""

from typing import Any, Dict, List, Optional
from decimal import Decimal


class CloudCostOptimizerError(Exception):
    """Base exception for all cloud cost optimizer errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(CloudCostOptimizerError):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_value: Any = None):
        super().__init__(message)
        self.invalid_value = invalid_value


class ResourceError(CloudCostOptimizerError):
    """Base class for resource-related errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a resource cannot be found."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.details = details or {}


class ResourceAccessError(ResourceError):
    """Raised when there are issues accessing resource data."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_id = resource_id
        self.details = details or {}


class MetricsError(CloudCostOptimizerError):
    """Base class for metrics-related errors."""
    pass


class MetricsCollectionError(MetricsError):
    """Raised when collecting resource metrics fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        metric_names: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.metric_names = metric_names
        self.details = details or {}


class MetricsAnalysisError(MetricsError):
    """Raised when analyzing metrics fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        analysis_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.analysis_type = analysis_type
        self.details = details or {}


class OptimizationError(CloudCostOptimizerError):
    """Base class for optimization-related errors."""
    pass


class OptimizationAnalysisError(OptimizationError):
    """Raised when optimization analysis fails."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        optimization_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.optimization_type = optimization_type
        self.details = details or {}


class OptimizationApplicationError(OptimizationError):
    """Raised when applying an optimization fails."""

    def __init__(
        self,
        message: str,
        recommendation_id: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.recommendation_id = recommendation_id
        self.resource_id = resource_id
        self.details = details or {}


class OptimizationRollbackError(OptimizationError):
    """Raised when rolling back an optimization fails."""

    def __init__(
        self,
        message: str,
        recommendation_id: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.recommendation_id = recommendation_id
        self.resource_id = resource_id
        self.details = details or {}


class PolicyError(CloudCostOptimizerError):
    """Base class for policy-related errors."""
    pass


class PolicyValidationError(PolicyError):
    """Raised when policy validation fails."""

    def __init__(
        self,
        message: str,
        policy_id: str,
        validation_errors: List[Dict[str, Any]]
    ):
        super().__init__(message)
        self.policy_id = policy_id
        self.validation_errors = validation_errors


class PolicyApplicationError(PolicyError):
    """Raised when applying a policy fails."""

    def __init__(
        self,
        message: str,
        policy_id: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.policy_id = policy_id
        self.resource_id = resource_id
        self.details = details or {}


class ComplianceError(CloudCostOptimizerError):
    """Base class for compliance-related errors."""
    pass


class ComplianceCheckError(ComplianceError):
    """Raised when a compliance check fails."""

    def __init__(
        self,
        message: str,
        check_id: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.check_id = check_id
        self.resource_id = resource_id
        self.details = details or {}


class ReportingError(CloudCostOptimizerError):
    """Base class for reporting-related errors."""
    pass


class ReportGenerationError(ReportingError):
    """Raised when report generation fails."""

    def __init__(
        self,
        message: str,
        report_type: str,
        time_period: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.report_type = report_type
        self.time_period = time_period
        self.details = details or {}


class CostCalculationError(CloudCostOptimizerError):
    """Raised when cost calculations fail."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        calculation_type: str,
        amount: Optional[Decimal] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.calculation_type = calculation_type
        self.amount = amount
        self.details = details or {}


class ProviderError(CloudCostOptimizerError):
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


class ConfigurationError(CloudCostOptimizerError):
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


class ConcurrencyError(CloudCostOptimizerError):
    """Raised when there are concurrent operation conflicts."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.operation = operation
        self.details = details or {}
