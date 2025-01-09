"""Custom exceptions for Cost Estimation Engine.

This module defines exceptions specific to cost estimation operations,
including pricing retrieval, model training, and prediction errors.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


class CostEstimationError(Exception):
    """Base exception for all cost estimation errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(CostEstimationError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(CostEstimationError):
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


class ProviderError(CostEstimationError):
    """Raised when there are issues with cloud providers."""

    def __init__(
        self,
        message: str,
        provider: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.details = details or {}


class PricingError(CostEstimationError):
    """Raised when there are issues retrieving pricing information."""

    def __init__(
        self,
        message: str,
        provider: str,
        resource_type: str,
        region: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.resource_type = resource_type
        self.region = region
        self.details = details or {}


class ModelTrainingError(CostEstimationError):
    """Raised when there are issues training estimation models."""

    def __init__(
        self,
        message: str,
        model_id: UUID,
        method: str,
        metrics: Optional[Dict[str, float]] = None
    ):
        super().__init__(message)
        self.model_id = model_id
        self.method = method
        self.metrics = metrics or {}


class PredictionError(CostEstimationError):
    """Raised when there are issues making cost predictions."""

    def __init__(
        self,
        message: str,
        model_id: UUID,
        resource_id: str,
        features: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.model_id = model_id
        self.resource_id = resource_id
        self.features = features or {}


class DataQualityError(CostEstimationError):
    """Raised when there are issues with data quality."""

    def __init__(
        self,
        message: str,
        data_source: str,
        quality_metrics: Dict[str, float],
        threshold: Optional[float] = None
    ):
        super().__init__(message)
        self.data_source = data_source
        self.quality_metrics = quality_metrics
        self.threshold = threshold


class FeatureEngineeringError(CostEstimationError):
    """Raised when there are issues with feature engineering."""

    def __init__(
        self,
        message: str,
        feature_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.feature_name = feature_name
        self.input_data = input_data


class ModelSelectionError(CostEstimationError):
    """Raised when there are issues selecting appropriate models."""

    def __init__(
        self,
        message: str,
        requirements: Dict[str, Any],
        available_models: List[str]
    ):
        super().__init__(message)
        self.requirements = requirements
        self.available_models = available_models


class OptimizationError(CostEstimationError):
    """Raised when there are issues with cost optimization."""

    def __init__(
        self,
        message: str,
        resource_id: str,
        current_cost: float,
        target_cost: Optional[float] = None
    ):
        super().__init__(message)
        self.resource_id = resource_id
        self.current_cost = current_cost
        self.target_cost = target_cost


class SensitivityAnalysisError(CostEstimationError):
    """Raised when there are issues with sensitivity analysis."""

    def __init__(
        self,
        message: str,
        variables: List[str],
        analysis_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.variables = variables
        self.analysis_type = analysis_type
        self.details = details or {}


class PerformanceError(CostEstimationError):
    """Raised when estimation performance is below threshold."""

    def __init__(
        self,
        message: str,
        operation: str,
        duration_ms: float,
        threshold_ms: float
    ):
        super().__init__(message)
        self.operation = operation
        self.duration_ms = duration_ms
        self.threshold_ms = threshold_ms


class DataSourceError(CostEstimationError):
    """Raised when there are issues with data sources."""

    def __init__(
        self,
        message: str,
        source: str,
        operation: str,
        last_successful: Optional[datetime] = None
    ):
        super().__init__(message)
        self.source = source
        self.operation = operation
        self.last_successful = last_successful


class CurrencyConversionError(CostEstimationError):
    """Raised when there are issues with currency conversion."""

    def __init__(
        self,
        message: str,
        from_currency: str,
        to_currency: str,
        amount: Optional[float] = None
    ):
        super().__init__(message)
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.amount = amount


class ResourceCompatibilityError(CostEstimationError):
    """Raised when resources are incompatible with estimation methods."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        estimation_method: str,
        requirements: Dict[str, Any]
    ):
        super().__init__(message)
        self.resource_type = resource_type
        self.estimation_method = estimation_method
        self.requirements = requirements


class EstimationTimeoutError(CostEstimationError):
    """Raised when estimation operations exceed time limits."""

    def __init__(
        self,
        message: str,
        operation: str,
        timeout_seconds: int,
        elapsed_seconds: float
    ):
        super().__init__(message)
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.elapsed_seconds = elapsed_seconds
