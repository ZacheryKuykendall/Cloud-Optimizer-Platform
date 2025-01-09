"""Data models for Cost Estimation Engine.

This module provides data models for estimating and predicting cloud resource costs
across different providers using various estimation methods and ML models.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set, Union, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"
    ORACLE = "ORACLE"
    ALIBABA = "ALIBABA"
    OTHER = "OTHER"


class ResourceType(str, Enum):
    """Types of cloud resources."""
    COMPUTE = "COMPUTE"
    STORAGE = "STORAGE"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    SERVERLESS = "SERVERLESS"
    CONTAINER = "CONTAINER"
    ANALYTICS = "ANALYTICS"
    CACHE = "CACHE"
    QUEUE = "QUEUE"
    OTHER = "OTHER"


class PricingModel(str, Enum):
    """Cloud resource pricing models."""
    ON_DEMAND = "ON_DEMAND"
    RESERVED = "RESERVED"
    SPOT = "SPOT"
    SAVINGS_PLAN = "SAVINGS_PLAN"
    COMMITTED_USE = "COMMITTED_USE"
    HYBRID = "HYBRID"


class BillingFrequency(str, Enum):
    """Billing frequency options."""
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    PER_REQUEST = "PER_REQUEST"
    PER_USE = "PER_USE"


class EstimationMethod(str, Enum):
    """Cost estimation methods."""
    DIRECT_PRICING = "DIRECT_PRICING"
    HISTORICAL_AVERAGE = "HISTORICAL_AVERAGE"
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    RANDOM_FOREST = "RANDOM_FOREST"
    GRADIENT_BOOSTING = "GRADIENT_BOOSTING"
    NEURAL_NETWORK = "NEURAL_NETWORK"
    PROPHET = "PROPHET"
    ENSEMBLE = "ENSEMBLE"


class ResourceMetrics(BaseModel):
    """Resource usage and performance metrics."""
    cpu_cores: Optional[float] = None
    memory_gb: Optional[float] = None
    storage_gb: Optional[float] = None
    iops: Optional[int] = None
    network_bandwidth_gbps: Optional[float] = None
    requests_per_second: Optional[float] = None
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class ResourceConfiguration(BaseModel):
    """Resource configuration details."""
    instance_type: Optional[str] = None
    region: str
    os_type: Optional[str] = None
    storage_type: Optional[str] = None
    performance_tier: Optional[str] = None
    availability_zone: Optional[str] = None
    commitment_term: Optional[int] = None  # in months
    features: Set[str] = Field(default_factory=set)
    settings: Dict[str, Any] = Field(default_factory=dict)


class PricingComponent(BaseModel):
    """Individual pricing component."""
    name: str
    unit: str
    rate: Decimal
    currency: str
    billing_frequency: BillingFrequency
    tiers: Optional[Dict[str, Decimal]] = None
    minimum_units: Optional[int] = None
    maximum_units: Optional[int] = None
    free_tier_units: Optional[int] = None


class ResourcePricing(BaseModel):
    """Resource pricing information."""
    id: UUID = Field(default_factory=uuid4)
    provider: CloudProvider
    resource_type: ResourceType
    pricing_model: PricingModel
    components: List[PricingComponent]
    effective_date: datetime
    expiration_date: Optional[datetime] = None
    region: str
    currency: str
    terms_and_conditions: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostDriver(BaseModel):
    """Cost driving factors."""
    name: str
    impact_weight: float
    correlation_coefficient: Optional[float] = None
    seasonality_pattern: Optional[str] = None
    trend_coefficient: Optional[float] = None
    variability_index: Optional[float] = None


class CostEstimate(BaseModel):
    """Cost estimate for a resource."""
    id: UUID = Field(default_factory=uuid4)
    resource_id: str
    provider: CloudProvider
    resource_type: ResourceType
    configuration: ResourceConfiguration
    pricing_model: PricingModel
    estimation_method: EstimationMethod
    time_period: timedelta
    estimated_cost: Decimal
    confidence_level: float
    accuracy_score: Optional[float] = None
    cost_breakdown: Dict[str, Decimal]
    cost_drivers: List[CostDriver]
    assumptions: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("estimated_cost", "confidence_level")
    def validate_positive(cls, v: Union[Decimal, float]) -> Union[Decimal, float]:
        """Validate positive values."""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class EstimationModel(BaseModel):
    """Machine learning model configuration."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    method: EstimationMethod
    features: List[str]
    target: str
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float]
    training_date: datetime
    version: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PredictionInterval(BaseModel):
    """Prediction interval for cost estimates."""
    lower_bound: Decimal
    upper_bound: Decimal
    confidence_level: float
    distribution_type: Optional[str] = None


class CostPrediction(BaseModel):
    """Future cost prediction."""
    id: UUID = Field(default_factory=uuid4)
    resource_id: str
    timestamp: datetime
    prediction_window: timedelta
    predicted_cost: Decimal
    prediction_interval: PredictionInterval
    model_id: UUID
    features_used: Dict[str, Any]
    prediction_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SensitivityAnalysis(BaseModel):
    """Cost sensitivity analysis."""
    id: UUID = Field(default_factory=uuid4)
    resource_id: str
    baseline_cost: Decimal
    variables: List[str]
    impacts: Dict[str, Dict[str, Decimal]]
    scenarios: Dict[str, Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class OptimizationOpportunity(BaseModel):
    """Cost optimization opportunity."""
    id: UUID = Field(default_factory=uuid4)
    resource_id: str
    opportunity_type: str
    current_cost: Decimal
    estimated_savings: Decimal
    implementation_effort: str
    risk_level: str
    prerequisites: List[str]
    steps: List[str]
    impact_assessment: Dict[str, Any]


class EstimationRequest(BaseModel):
    """Request for cost estimation."""
    provider: CloudProvider
    resource_type: ResourceType
    configuration: ResourceConfiguration
    pricing_model: Optional[PricingModel] = None
    estimation_method: Optional[EstimationMethod] = None
    time_period: Optional[timedelta] = None
    include_optimization: bool = False
    include_sensitivity: bool = False
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)


class EstimationResponse(BaseModel):
    """Response containing cost estimation results."""
    request_id: UUID = Field(default_factory=uuid4)
    estimate: CostEstimate
    predictions: Optional[List[CostPrediction]] = None
    sensitivity: Optional[SensitivityAnalysis] = None
    opportunities: Optional[List[OptimizationOpportunity]] = None
    alternatives: Optional[List[CostEstimate]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
