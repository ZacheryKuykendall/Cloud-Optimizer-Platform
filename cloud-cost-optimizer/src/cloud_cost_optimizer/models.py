"""Data models for cloud cost optimization.

This module provides data models for analyzing cloud resource usage and
generating cost optimization recommendations.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ResourceType(str, Enum):
    """Types of cloud resources."""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    SERVERLESS = "serverless"
    CONTAINER = "container"
    ANALYTICS = "analytics"
    SECURITY = "security"
    MANAGEMENT = "management"
    OTHER = "other"


class OptimizationType(str, Enum):
    """Types of cost optimizations."""
    RIGHTSIZING = "rightsizing"  # e.g., resize underutilized instances
    SCHEDULING = "scheduling"  # e.g., start/stop based on usage patterns
    MODERNIZATION = "modernization"  # e.g., move to serverless/containers
    RESERVATION = "reservation"  # e.g., reserved instances/savings plans
    CLEANUP = "cleanup"  # e.g., remove unused resources
    STORAGE_TIER = "storage_tier"  # e.g., move to cheaper storage tiers
    NETWORKING = "networking"  # e.g., optimize data transfer costs


class SeverityLevel(str, Enum):
    """Severity levels for recommendations."""
    HIGH = "high"  # Significant cost impact
    MEDIUM = "medium"  # Moderate cost impact
    LOW = "low"  # Minor cost impact


class ResourceMetrics(BaseModel):
    """Resource utilization metrics."""
    cpu_utilization: Optional[float] = None  # Percentage
    memory_utilization: Optional[float] = None  # Percentage
    disk_iops: Optional[float] = None  # IOPS
    network_in: Optional[float] = None  # Bytes/sec
    network_out: Optional[float] = None  # Bytes/sec
    requests_per_second: Optional[float] = None  # RPS
    average_latency: Optional[float] = None  # Milliseconds
    error_rate: Optional[float] = None  # Percentage
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ResourceUsagePattern(BaseModel):
    """Resource usage pattern analysis."""
    peak_hours: Set[int] = Field(default_factory=set)  # Hours with peak usage
    low_usage_hours: Set[int] = Field(default_factory=set)  # Hours with low usage
    weekend_usage: bool = False  # Whether resource is used on weekends
    usage_trend: str = "stable"  # stable, increasing, decreasing
    last_accessed: Optional[datetime] = None
    access_frequency: Optional[str] = None  # frequent, occasional, rare


class ResourceCost(BaseModel):
    """Resource cost information."""
    hourly_cost: Decimal
    monthly_cost: Decimal
    currency: str = "USD"
    last_billing_cycle: Optional[datetime] = None
    cost_trend: str = "stable"  # stable, increasing, decreasing
    breakdown: Dict[str, Decimal] = Field(default_factory=dict)


class OptimizationRecommendation(BaseModel):
    """Cost optimization recommendation."""
    id: str
    resource_id: str
    resource_type: ResourceType
    provider: CloudProvider
    optimization_type: OptimizationType
    severity: SeverityLevel
    current_cost: ResourceCost
    estimated_savings: ResourceCost
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    description: str
    justification: str
    action_items: List[str]
    prerequisites: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class ResourceConfiguration(BaseModel):
    """Resource configuration details."""
    provider: CloudProvider
    resource_type: ResourceType
    resource_id: str
    name: str
    region: str
    specifications: Dict[str, str] = Field(default_factory=dict)
    tags: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    owner: Optional[str] = None
    environment: Optional[str] = None
    project: Optional[str] = None


class OptimizationResult(BaseModel):
    """Result of applying an optimization."""
    recommendation_id: str
    resource_id: str
    status: str  # success, failed, in_progress
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    actual_savings: Optional[ResourceCost] = None
    issues: List[str] = Field(default_factory=list)
    rollback_status: Optional[str] = None
    validation_results: Dict[str, bool] = Field(default_factory=dict)


class ResourceAnalysis(BaseModel):
    """Complete resource analysis."""
    resource: ResourceConfiguration
    metrics: ResourceMetrics
    usage_pattern: ResourceUsagePattern
    current_cost: ResourceCost
    recommendations: List[OptimizationRecommendation] = Field(default_factory=list)
    optimization_history: List[OptimizationResult] = Field(default_factory=list)
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)


class OptimizationSummary(BaseModel):
    """Summary of optimization recommendations."""
    total_resources_analyzed: int
    resources_with_recommendations: int
    total_recommendations: int
    total_potential_savings: ResourceCost
    recommendations_by_type: Dict[OptimizationType, int] = Field(default_factory=dict)
    recommendations_by_severity: Dict[SeverityLevel, int] = Field(default_factory=dict)
    savings_by_provider: Dict[CloudProvider, ResourceCost] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizationPolicy(BaseModel):
    """Policy for automated optimizations."""
    id: str
    name: str
    description: str
    enabled: bool = True
    resource_types: Set[ResourceType] = Field(default_factory=set)
    providers: Set[CloudProvider] = Field(default_factory=set)
    optimization_types: Set[OptimizationType] = Field(default_factory=set)
    auto_approve: bool = False
    approval_required_above: Optional[Decimal] = None
    excluded_resources: Set[str] = Field(default_factory=set)
    schedule: Optional[str] = None  # Cron expression
    notification_channels: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = Field(default_factory=dict)


class OptimizationEvent(BaseModel):
    """Event related to optimization activities."""
    id: str
    event_type: str
    resource_id: str
    recommendation_id: Optional[str] = None
    policy_id: Optional[str] = None
    description: str
    details: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str = "info"  # info, warning, error
    metadata: Dict[str, str] = Field(default_factory=dict)


class ComplianceCheck(BaseModel):
    """Compliance check for optimizations."""
    id: str
    name: str
    description: str
    resource_id: str
    check_type: str
    result: bool
    details: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = Field(default_factory=dict)


class OptimizationReport(BaseModel):
    """Detailed optimization report."""
    id: str
    report_type: str
    time_period: str
    summary: OptimizationSummary
    resource_analyses: List[ResourceAnalysis]
    applied_optimizations: List[OptimizationResult]
    compliance_checks: List[ComplianceCheck]
    events: List[OptimizationEvent]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = Field(default_factory=dict)
