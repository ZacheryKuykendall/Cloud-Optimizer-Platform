"""Data models for cloud budget management.

This module provides data models for tracking and managing cloud budgets,
spending alerts, and cost forecasts across different cloud providers.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, validator


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class BudgetPeriod(str, Enum):
    """Budget time periods."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class BudgetCategory(str, Enum):
    """Budget categories for different types of spending."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    ANALYTICS = "analytics"
    SECURITY = "security"
    SUPPORT = "support"
    OTHER = "other"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class SpendingTrend(str, Enum):
    """Spending trend indicators."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class ForecastAccuracy(str, Enum):
    """Forecast accuracy levels."""
    HIGH = "high"  # < 5% error
    MEDIUM = "medium"  # 5-15% error
    LOW = "low"  # > 15% error


class BudgetThreshold(BaseModel):
    """Budget threshold configuration."""
    percentage: float = Field(..., ge=0, le=200)
    amount: Decimal
    alert_enabled: bool = True
    notification_channels: List[str] = Field(default_factory=list)


class BudgetFilter(BaseModel):
    """Budget filtering criteria."""
    providers: Optional[Set[CloudProvider]] = None
    categories: Optional[Set[BudgetCategory]] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    regions: Optional[Set[str]] = None
    services: Optional[Set[str]] = None


class Budget(BaseModel):
    """Cloud budget configuration."""
    id: str
    name: str
    description: Optional[str] = None
    amount: Decimal
    currency: str = "USD"
    period: BudgetPeriod
    start_date: datetime
    end_date: Optional[datetime] = None
    filters: BudgetFilter
    thresholds: List[BudgetThreshold]
    auto_adjust: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    tags: Dict[str, str] = Field(default_factory=dict)

    @validator("thresholds")
    def validate_thresholds(cls, v):
        """Validate budget thresholds."""
        if not v:
            raise ValueError("At least one threshold must be defined")
        if any(t.percentage > 200 for t in v):
            raise ValueError("Threshold percentage cannot exceed 200%")
        return sorted(v, key=lambda x: x.percentage)


class SpendingAlert(BaseModel):
    """Budget spending alert."""
    id: str
    budget_id: str
    threshold: float
    actual_spend: Decimal
    forecasted_spend: Optional[Decimal] = None
    severity: AlertSeverity
    status: AlertStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class SpendingMetrics(BaseModel):
    """Current spending metrics."""
    total_spend: Decimal
    daily_average: Decimal
    peak_daily_spend: Decimal
    lowest_daily_spend: Decimal
    trend: SpendingTrend
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class CategorySpending(BaseModel):
    """Spending breakdown by category."""
    category: BudgetCategory
    amount: Decimal
    percentage: float
    trend: SpendingTrend
    previous_period_amount: Optional[Decimal] = None
    change_percentage: Optional[float] = None


class ProviderSpending(BaseModel):
    """Spending breakdown by provider."""
    provider: CloudProvider
    amount: Decimal
    percentage: float
    trend: SpendingTrend
    previous_period_amount: Optional[Decimal] = None
    change_percentage: Optional[float] = None


class SpendingForecast(BaseModel):
    """Spending forecast."""
    forecasted_amount: Decimal
    confidence_interval: tuple[Decimal, Decimal]
    accuracy: ForecastAccuracy
    trend: SpendingTrend
    contributing_factors: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    forecast_period_start: datetime
    forecast_period_end: datetime


class BudgetSummary(BaseModel):
    """Budget status summary."""
    budget: Budget
    current_spend: Decimal
    remaining_budget: Decimal
    percentage_used: float
    percentage_time_elapsed: float
    spending_metrics: SpendingMetrics
    category_breakdown: List[CategorySpending]
    provider_breakdown: List[ProviderSpending]
    active_alerts: List[SpendingAlert]
    forecast: SpendingForecast


class BudgetAdjustmentRecommendation(BaseModel):
    """Budget adjustment recommendation."""
    budget_id: str
    current_amount: Decimal
    recommended_amount: Decimal
    adjustment_percentage: float
    justification: str
    confidence: float
    historical_data_points: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetQuery(BaseModel):
    """Query parameters for budget search."""
    providers: Optional[List[CloudProvider]] = None
    categories: Optional[List[BudgetCategory]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    period: Optional[BudgetPeriod] = None
    tags: Optional[Dict[str, str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_alerts: Optional[bool] = None


class BudgetState(BaseModel):
    """Current state of all budgets."""
    budgets: Dict[str, Budget]  # Budget ID -> Budget
    alerts: Dict[str, List[SpendingAlert]]  # Budget ID -> Alerts
    summaries: Dict[str, BudgetSummary]  # Budget ID -> Summary
    recommendations: Dict[str, BudgetAdjustmentRecommendation]  # Budget ID -> Recommendation
    last_updated: datetime = Field(default_factory=datetime.utcnow)
