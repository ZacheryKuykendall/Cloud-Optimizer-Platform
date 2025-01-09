"""Custom exceptions for provider selection service.

This module defines exceptions specific to making decisions about
resource placement across different cloud providers.
"""

from typing import Any, Dict, List, Optional, Set


class ProviderSelectionError(Exception):
    """Base exception for all provider selection errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ValidationError(ProviderSelectionError):
    """Raised when resource requirements validation fails."""

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


class NoMatchingProvidersError(ProviderSelectionError):
    """Raised when no providers match the specified requirements."""

    def __init__(
        self,
        message: str,
        requirements: Dict[str, Any],
        checked_providers: List[str],
        failure_reasons: Dict[str, str]
    ):
        super().__init__(
            message,
            details={
                "requirements": requirements,
                "checked_providers": checked_providers,
                "failure_reasons": failure_reasons
            }
        )
        self.requirements = requirements
        self.checked_providers = checked_providers
        self.failure_reasons = failure_reasons


class CapabilityMatchError(ProviderSelectionError):
    """Raised when provider capabilities don't match requirements."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        missing_capabilities: Set[str],
        available_capabilities: Set[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "resource_type": resource_type,
                "missing_capabilities": list(missing_capabilities),
                "available_capabilities": list(available_capabilities)
            }
        )
        self.provider = provider
        self.resource_type = resource_type
        self.missing_capabilities = missing_capabilities
        self.available_capabilities = available_capabilities


class ComplianceError(ProviderSelectionError):
    """Raised when compliance requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        required_frameworks: Set[str],
        available_frameworks: Set[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "resource_type": resource_type,
                "required_frameworks": list(required_frameworks),
                "available_frameworks": list(available_frameworks)
            }
        )
        self.provider = provider
        self.resource_type = resource_type
        self.required_frameworks = required_frameworks
        self.available_frameworks = available_frameworks


class PerformanceError(ProviderSelectionError):
    """Raised when performance requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        metric: str,
        required_value: float,
        available_value: float
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "resource_type": resource_type,
                "metric": metric,
                "required_value": required_value,
                "available_value": available_value
            }
        )
        self.provider = provider
        self.resource_type = resource_type
        self.metric = metric
        self.required_value = required_value
        self.available_value = available_value


class BudgetError(ProviderSelectionError):
    """Raised when cost requirements cannot be met."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        max_budget: float,
        estimated_cost: float
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "resource_type": resource_type,
                "max_budget": max_budget,
                "estimated_cost": estimated_cost
            }
        )
        self.provider = provider
        self.resource_type = resource_type
        self.max_budget = max_budget
        self.estimated_cost = estimated_cost


class RuleEvaluationError(ProviderSelectionError):
    """Raised when rule evaluation fails."""

    def __init__(
        self,
        message: str,
        rule_name: str,
        condition: str,
        error_type: str,
        error_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "rule_name": rule_name,
                "condition": condition,
                "error_type": error_type,
                "error_details": error_details or {}
            }
        )
        self.rule_name = rule_name
        self.condition = condition
        self.error_type = error_type
        self.error_details = error_details or {}


class PolicyValidationError(ProviderSelectionError):
    """Raised when policy validation fails."""

    def __init__(
        self,
        message: str,
        policy_name: str,
        validation_errors: Dict[str, List[str]]
    ):
        super().__init__(
            message,
            details={
                "policy_name": policy_name,
                "validation_errors": validation_errors
            }
        )
        self.policy_name = policy_name
        self.validation_errors = validation_errors


class RegionAvailabilityError(ProviderSelectionError):
    """Raised when required regions are not available."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        required_regions: Set[str],
        available_regions: Set[str]
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "resource_type": resource_type,
                "required_regions": list(required_regions),
                "available_regions": list(available_regions)
            }
        )
        self.provider = provider
        self.resource_type = resource_type
        self.required_regions = required_regions
        self.available_regions = available_regions


class DependencyError(ProviderSelectionError):
    """Raised when resource dependencies cannot be satisfied."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        missing_dependencies: List[str],
        dependency_errors: Dict[str, str]
    ):
        super().__init__(
            message,
            details={
                "resource_name": resource_name,
                "missing_dependencies": missing_dependencies,
                "dependency_errors": dependency_errors
            }
        )
        self.resource_name = resource_name
        self.missing_dependencies = missing_dependencies
        self.dependency_errors = dependency_errors


class ScoreCalculationError(ProviderSelectionError):
    """Raised when provider scoring fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        scoring_component: str,
        error_details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            details={
                "provider": provider,
                "resource_type": resource_type,
                "scoring_component": scoring_component,
                "error_details": error_details or {}
            }
        )
        self.provider = provider
        self.resource_type = resource_type
        self.scoring_component = scoring_component
        self.error_details = error_details or {}


class SelectionTimeoutError(ProviderSelectionError):
    """Raised when provider selection times out."""

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


class ConcurrencyError(ProviderSelectionError):
    """Raised when concurrent selection operations conflict."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        conflicting_operation: str,
        operation_id: str
    ):
        super().__init__(
            message,
            details={
                "resource_name": resource_name,
                "conflicting_operation": conflicting_operation,
                "operation_id": operation_id
            }
        )
        self.resource_name = resource_name
        self.conflicting_operation = conflicting_operation
        self.operation_id = operation_id
