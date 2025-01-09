"""Custom exceptions for Terraform cost analysis.

This module defines exceptions specific to Terraform cost analysis operations,
including plan parsing, cost estimation, and provider-specific errors.
"""

from typing import Any, Dict, List, Optional


class TerraformCostAnalyzerError(Exception):
    """Base exception for all Terraform cost analyzer errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(TerraformCostAnalyzerError):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_value: Any = None):
        super().__init__(message)
        self.invalid_value = invalid_value


class PlanParsingError(TerraformCostAnalyzerError):
    """Raised when parsing a Terraform plan fails."""

    def __init__(
        self,
        message: str,
        plan_file: Optional[str] = None,
        line_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.plan_file = plan_file
        self.line_number = line_number
        self.details = details or {}


class ResourceParsingError(PlanParsingError):
    """Raised when parsing a specific resource in the plan fails."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_name = resource_name


class ModuleParsingError(PlanParsingError):
    """Raised when parsing a Terraform module fails."""

    def __init__(
        self,
        message: str,
        module_name: Optional[str] = None,
        module_source: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.module_name = module_name
        self.module_source = module_source


class ProviderError(TerraformCostAnalyzerError):
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


class ResourceMappingError(TerraformCostAnalyzerError):
    """Raised when resource type mapping fails."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        available_mappings: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_type = resource_type
        self.available_mappings = available_mappings


class PricingError(TerraformCostAnalyzerError):
    """Base class for pricing-related errors."""
    pass


class PricingDataNotFoundError(PricingError):
    """Raised when pricing data is not available."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        region: Optional[str] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_type = resource_type
        self.region = region


class PricingCalculationError(PricingError):
    """Raised when cost calculation fails."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        pricing_tier: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_type = resource_type
        self.pricing_tier = pricing_tier
        self.details = details or {}


class UsageEstimationError(TerraformCostAnalyzerError):
    """Raised when usage estimation fails."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        metric: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_type = resource_type
        self.metric = metric
        self.details = details or {}


class ConfigurationError(TerraformCostAnalyzerError):
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


class CacheError(TerraformCostAnalyzerError):
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


class StateError(TerraformCostAnalyzerError):
    """Raised when there are issues with Terraform state."""

    def __init__(
        self,
        message: str,
        state_file: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.state_file = state_file
        self.details = details or {}


class DiffError(TerraformCostAnalyzerError):
    """Raised when there are issues comparing costs."""

    def __init__(
        self,
        message: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.details = details or {}


class OutputFormattingError(TerraformCostAnalyzerError):
    """Raised when there are issues formatting the output."""

    def __init__(
        self,
        message: str,
        format_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.format_type = format_type
        self.details = details or {}
