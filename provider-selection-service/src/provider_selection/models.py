"""Data models for provider selection service.

This module provides data models for making intelligent decisions about
resource placement across different cloud providers.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """Types of cloud resources."""
    COMPUTE = "compute"  # VMs, containers, serverless
    STORAGE = "storage"  # Block, object, file storage
    NETWORK = "network"  # VPC, load balancers, CDN, etc.
    DATABASE = "database"  # Managed databases
    CACHE = "cache"  # In-memory caching
    QUEUE = "queue"  # Message queues
    ANALYTICS = "analytics"  # Data analytics services
    AI = "ai"  # AI/ML services


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    HIPAA = "hipaa"  # Healthcare
    PCI = "pci"  # Payment card industry
    SOC2 = "soc2"  # Service organization controls
    GDPR = "gdpr"  # EU data protection
    ISO27001 = "iso27001"  # Information security
    FEDRAMP = "fedramp"  # US federal government
    NIST = "nist"  # National Institute of Standards and Technology
    SOX = "sox"  # Sarbanes-Oxley


class PerformanceMetric(str, Enum):
    """Performance metrics for resources."""
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    DISK_IOPS = "disk_iops"
    DISK_THROUGHPUT = "disk_throughput"
    NETWORK_LATENCY = "network_latency"
    NETWORK_THROUGHPUT = "network_throughput"
    REQUEST_RATE = "request_rate"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"


class ResourceRequirements(BaseModel):
    """Requirements for a cloud resource."""
    resource_type: ResourceType
    name: str
    description: Optional[str] = None
    regions: Set[str]
    min_availability: float = Field(ge=0.0, le=100.0)  # Percentage
    max_latency_ms: Optional[float] = None
    required_features: Set[str] = Field(default_factory=set)
    required_certifications: Set[str] = Field(default_factory=set)
    compliance_frameworks: Set[ComplianceFramework] = Field(default_factory=set)
    performance_targets: Dict[PerformanceMetric, float] = Field(default_factory=dict)
    max_monthly_budget: Optional[Decimal] = None
    preferred_providers: Optional[Set[str]] = None
    excluded_providers: Optional[Set[str]] = None
    dependencies: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)

    # Resource-specific requirements
    compute_requirements: Optional[Dict[str, Any]] = None
    storage_requirements: Optional[Dict[str, Any]] = None
    network_requirements: Optional[Dict[str, Any]] = None
    database_requirements: Optional[Dict[str, Any]] = None
    cache_requirements: Optional[Dict[str, Any]] = None
    queue_requirements: Optional[Dict[str, Any]] = None
    analytics_requirements: Optional[Dict[str, Any]] = None
    ai_requirements: Optional[Dict[str, Any]] = None


class ProviderCapability(BaseModel):
    """Provider capability for a specific resource type."""
    provider: str
    resource_type: ResourceType
    region: str
    features: Set[str]
    certifications: Set[str]
    compliance_frameworks: Set[ComplianceFramework]
    performance_metrics: Dict[PerformanceMetric, float]
    availability_sla: float
    pricing_model: Dict[str, Any]
    limitations: Optional[Dict[str, Any]] = None


class CostEstimate(BaseModel):
    """Cost estimate for a resource on a provider."""
    provider: str
    resource_type: ResourceType
    region: str
    monthly_cost: Decimal
    setup_cost: Optional[Decimal] = None
    egress_cost: Optional[Decimal] = None
    storage_cost: Optional[Decimal] = None
    compute_cost: Optional[Decimal] = None
    network_cost: Optional[Decimal] = None
    other_costs: Dict[str, Decimal] = Field(default_factory=dict)
    pricing_details: Dict[str, Any] = Field(default_factory=dict)


class PerformanceScore(BaseModel):
    """Performance score for a provider option."""
    provider: str
    resource_type: ResourceType
    region: str
    latency_score: float = Field(ge=0.0, le=1.0)
    throughput_score: float = Field(ge=0.0, le=1.0)
    reliability_score: float = Field(ge=0.0, le=1.0)
    scalability_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)
    metrics: Dict[PerformanceMetric, float]


class ComplianceScore(BaseModel):
    """Compliance score for a provider option."""
    provider: str
    resource_type: ResourceType
    region: str
    framework_scores: Dict[ComplianceFramework, float]
    certification_coverage: float = Field(ge=0.0, le=1.0)
    feature_coverage: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)


class ProviderOption(BaseModel):
    """Provider option for a resource."""
    provider: str
    resource_type: ResourceType
    region: str
    capability: ProviderCapability
    cost_estimate: CostEstimate
    performance_score: PerformanceScore
    compliance_score: ComplianceScore
    total_score: float = Field(ge=0.0, le=1.0)
    ranking_factors: Dict[str, float]
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class SelectionResult(BaseModel):
    """Result of provider selection process."""
    resource_requirements: ResourceRequirements
    selected_option: ProviderOption
    alternative_options: List[ProviderOption]
    selection_factors: Dict[str, float]
    cost_comparison: Dict[str, CostEstimate]
    performance_comparison: Dict[str, PerformanceScore]
    compliance_comparison: Dict[str, ComplianceScore]
    selection_date: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SelectionRule(BaseModel):
    """Rule for provider selection."""
    name: str
    description: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    condition: str  # Python expression
    weight: float = Field(ge=0.0, le=1.0)
    priority: int = Field(ge=0)
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleEvaluation(BaseModel):
    """Result of rule evaluation."""
    rule: SelectionRule
    provider_option: ProviderOption
    condition_result: bool
    score_contribution: float
    factors: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SelectionPolicy(BaseModel):
    """Policy for provider selection."""
    name: str
    description: Optional[str] = None
    rules: List[SelectionRule]
    default_weights: Dict[str, float]
    override_rules: Dict[str, List[str]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluation(BaseModel):
    """Result of policy evaluation."""
    policy: SelectionPolicy
    resource_requirements: ResourceRequirements
    provider_options: List[ProviderOption]
    rule_evaluations: List[RuleEvaluation]
    selected_option: ProviderOption
    evaluation_date: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
