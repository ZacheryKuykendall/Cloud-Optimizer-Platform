"""Cost Estimation Engine

An engine for estimating and predicting cloud resource costs across different providers
using various estimation methods and machine learning models.
"""

from cost_estimation.models import (
    CloudProvider,
    ResourceType,
    PricingModel,
    BillingFrequency,
    EstimationMethod,
    ResourceMetrics,
    ResourceConfiguration,
    PricingComponent,
    ResourcePricing,
    CostDriver,
    CostEstimate,
    EstimationModel,
    PredictionInterval,
    CostPrediction,
    SensitivityAnalysis,
    OptimizationOpportunity,
    EstimationRequest,
    EstimationResponse,
)
from cost_estimation.exceptions import (
    CostEstimationError,
    ValidationError,
    ConfigurationError,
    ProviderError,
    PricingError,
    ModelTrainingError,
    PredictionError,
    DataQualityError,
    FeatureEngineeringError,
    ModelSelectionError,
    OptimizationError,
    SensitivityAnalysisError,
    PerformanceError,
    DataSourceError,
    CurrencyConversionError,
    ResourceCompatibilityError,
    EstimationTimeoutError,
)

__version__ = "0.1.0"

__all__ = [
    # Cloud Providers and Resource Types
    "CloudProvider",
    "ResourceType",
    "PricingModel",
    "BillingFrequency",
    "EstimationMethod",

    # Core Models
    "ResourceMetrics",
    "ResourceConfiguration",
    "PricingComponent",
    "ResourcePricing",
    "CostDriver",
    "CostEstimate",

    # Estimation and Prediction
    "EstimationModel",
    "PredictionInterval",
    "CostPrediction",
    "SensitivityAnalysis",
    "OptimizationOpportunity",

    # Request/Response Models
    "EstimationRequest",
    "EstimationResponse",

    # Base Exceptions
    "CostEstimationError",
    "ValidationError",
    "ConfigurationError",

    # Provider and Pricing Exceptions
    "ProviderError",
    "PricingError",
    "CurrencyConversionError",

    # Model and Prediction Exceptions
    "ModelTrainingError",
    "PredictionError",
    "ModelSelectionError",
    "ResourceCompatibilityError",

    # Data and Feature Exceptions
    "DataQualityError",
    "FeatureEngineeringError",
    "DataSourceError",

    # Analysis Exceptions
    "OptimizationError",
    "SensitivityAnalysisError",

    # System Exceptions
    "PerformanceError",
    "EstimationTimeoutError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
