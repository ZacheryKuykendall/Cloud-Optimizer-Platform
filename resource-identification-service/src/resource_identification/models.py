"""Data models for Resource Identification Service.

This module provides data models for identifying and classifying cloud resources
across different providers.
"""

from datetime import datetime
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
    SECURITY = "SECURITY"
    ANALYTICS = "ANALYTICS"
    SERVERLESS = "SERVERLESS"
    CONTAINER = "CONTAINER"
    MESSAGING = "MESSAGING"
    MONITORING = "MONITORING"
    OTHER = "OTHER"


class ResourceStatus(str, Enum):
    """Status of cloud resources."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    STOPPED = "STOPPED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ResourceTier(str, Enum):
    """Resource performance tiers."""
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    TESTING = "TESTING"
    SANDBOX = "SANDBOX"


class ResourceClassification(str, Enum):
    """Resource classification categories."""
    CRITICAL = "CRITICAL"
    IMPORTANT = "IMPORTANT"
    STANDARD = "STANDARD"
    EXPERIMENTAL = "EXPERIMENTAL"
    DEPRECATED = "DEPRECATED"


class ResourceDependencyType(str, Enum):
    """Types of resource dependencies."""
    REQUIRES = "REQUIRES"
    USED_BY = "USED_BY"
    CONNECTS_TO = "CONNECTS_TO"
    PART_OF = "PART_OF"
    MANAGES = "MANAGES"


class ResourceMetadata(BaseModel):
    """Metadata for cloud resources."""
    creation_date: datetime
    last_modified: datetime
    region: str
    zone: Optional[str] = None
    account_id: str
    project_id: Optional[str] = None
    subscription_id: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class ResourceDependency(BaseModel):
    """Model for resource dependencies."""
    id: UUID = Field(default_factory=uuid4)
    source_id: str
    target_id: str
    dependency_type: ResourceDependencyType
    attributes: Dict[str, Any] = Field(default_factory=dict)
    is_critical: bool = False
    description: Optional[str] = None


class ResourceUsage(BaseModel):
    """Resource usage metrics."""
    timestamp: datetime
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    disk_utilization: Optional[float] = None
    network_in: Optional[float] = None
    network_out: Optional[float] = None
    requests_per_second: Optional[float] = None
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class ResourceConfiguration(BaseModel):
    """Resource configuration details."""
    size: Optional[str] = None
    capacity: Optional[str] = None
    version: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    features: Set[str] = Field(default_factory=set)
    limits: Dict[str, Union[int, float, str]] = Field(default_factory=dict)
    network_config: Dict[str, Any] = Field(default_factory=dict)
    security_config: Dict[str, Any] = Field(default_factory=dict)


class CloudResource(BaseModel):
    """Model for cloud resources."""
    id: UUID = Field(default_factory=uuid4)
    provider: CloudProvider
    provider_id: str
    name: str
    type: ResourceType
    status: ResourceStatus
    tier: ResourceTier
    classification: ResourceClassification
    metadata: ResourceMetadata
    configuration: ResourceConfiguration
    usage: Optional[ResourceUsage] = None
    dependencies: List[ResourceDependency] = Field(default_factory=list)
    cost_allocation: Dict[str, float] = Field(default_factory=dict)
    compliance_status: Dict[str, bool] = Field(default_factory=dict)
    last_scan: datetime = Field(default_factory=datetime.utcnow)

    @validator("provider_id")
    def validate_provider_id(cls, v: str) -> str:
        """Validate provider ID format."""
        if not v:
            raise ValueError("Provider ID cannot be empty")
        return v


class ResourceScanConfig(BaseModel):
    """Configuration for resource scanning."""
    providers: List[CloudProvider]
    regions: List[str]
    resource_types: Optional[List[ResourceType]] = None
    include_inactive: bool = False
    scan_dependencies: bool = True
    max_depth: int = 3
    parallel_scans: int = 5
    timeout_seconds: int = 300
    custom_filters: Dict[str, Any] = Field(default_factory=dict)


class ResourceScanResult(BaseModel):
    """Results from a resource scan."""
    id: UUID = Field(default_factory=uuid4)
    config: ResourceScanConfig
    start_time: datetime
    end_time: Optional[datetime] = None
    resources: List[CloudResource] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)


class ResourceQuery(BaseModel):
    """Query parameters for resource search."""
    providers: Optional[List[CloudProvider]] = None
    types: Optional[List[ResourceType]] = None
    statuses: Optional[List[ResourceStatus]] = None
    regions: Optional[List[str]] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    name_pattern: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    include_dependencies: bool = False
    include_usage: bool = False
    custom_filters: Dict[str, Any] = Field(default_factory=dict)


class ResourceClassificationRule(BaseModel):
    """Rules for automatic resource classification."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    provider: Optional[CloudProvider] = None
    resource_type: Optional[ResourceType] = None
    conditions: List[Dict[str, Any]]
    classification: ResourceClassification
    priority: int = 0
    enabled: bool = True


class ResourceDependencyGraph(BaseModel):
    """Graph representation of resource dependencies."""
    id: UUID = Field(default_factory=uuid4)
    resources: List[CloudResource]
    dependencies: List[ResourceDependency]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    analysis: Dict[str, Any] = Field(default_factory=dict)
