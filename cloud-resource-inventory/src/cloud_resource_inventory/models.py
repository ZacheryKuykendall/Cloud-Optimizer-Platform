"""Data models for cloud resource inventory.

This module provides data models for tracking and managing cloud resources
across different providers.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ResourceType(str, Enum):
    """Types of cloud resources."""
    COMPUTE = "compute"  # EC2, VM, GCE
    STORAGE = "storage"  # S3, Blob Storage, GCS
    DATABASE = "database"  # RDS, CosmosDB, Cloud SQL
    NETWORK = "network"  # VPC, VNet, VPC Network
    CONTAINER = "container"  # ECS, AKS, GKE
    SERVERLESS = "serverless"  # Lambda, Functions, Cloud Functions
    CACHE = "cache"  # ElastiCache, Redis Cache, Memorystore
    QUEUE = "queue"  # SQS, Service Bus, Pub/Sub
    LOAD_BALANCER = "load_balancer"  # ELB, Load Balancer, Cloud Load Balancing
    DNS = "dns"  # Route53, DNS, Cloud DNS
    CDN = "cdn"  # CloudFront, CDN, Cloud CDN
    MONITORING = "monitoring"  # CloudWatch, Monitor, Cloud Monitoring
    IDENTITY = "identity"  # IAM, Active Directory, Cloud Identity
    SECURITY = "security"  # WAF, Security Center, Cloud Armor
    OTHER = "other"


class ResourceStatus(str, Enum):
    """Status of a cloud resource."""
    ACTIVE = "active"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    FAILED = "failed"
    CREATING = "creating"
    UPDATING = "updating"
    DELETING = "deleting"
    UNKNOWN = "unknown"


class ResourceLifecycle(str, Enum):
    """Lifecycle stage of a resource."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ResourceCriticality(str, Enum):
    """Criticality level of a resource."""
    HIGH = "high"  # Mission-critical resources
    MEDIUM = "medium"  # Important but not critical
    LOW = "low"  # Non-critical resources


class ResourceTag(BaseModel):
    """Tag associated with a resource."""
    key: str
    value: str
    provider_specific: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResourceMetadata(BaseModel):
    """Metadata associated with a resource."""
    created_by: str
    created_at: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    version: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class ResourceDependency(BaseModel):
    """Dependency relationship between resources."""
    resource_id: str
    dependency_type: str  # e.g., "requires", "uses", "connects_to"
    direction: str  # "inbound" or "outbound"
    criticality: ResourceCriticality
    description: Optional[str] = None


class ResourceCompliance(BaseModel):
    """Compliance status of a resource."""
    framework: str  # e.g., "HIPAA", "PCI", "SOC2"
    status: bool
    last_checked: datetime
    details: Dict[str, str] = Field(default_factory=dict)
    violations: List[str] = Field(default_factory=list)
    exemptions: List[str] = Field(default_factory=list)


class ResourceCost(BaseModel):
    """Cost information for a resource."""
    hourly_cost: float
    monthly_cost: float
    currency: str = "USD"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    cost_components: Dict[str, float] = Field(default_factory=dict)
    tags: Dict[str, str] = Field(default_factory=dict)


class ResourceConfiguration(BaseModel):
    """Configuration of a cloud resource."""
    provider_specific_config: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    version_history: List[Dict[str, Any]] = Field(default_factory=list)


class ResourcePermission(BaseModel):
    """Permission associated with a resource."""
    principal: str  # User, role, or service
    action: str  # The allowed action
    effect: str  # "allow" or "deny"
    condition: Optional[Dict[str, Any]] = None


class ResourceAuditLog(BaseModel):
    """Audit log entry for a resource."""
    timestamp: datetime
    action: str
    principal: str
    details: Dict[str, Any]
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None


class ResourceBackup(BaseModel):
    """Backup information for a resource."""
    backup_id: str
    created_at: datetime
    status: str
    size_bytes: int
    retention_days: int
    encrypted: bool
    location: str
    metadata: Dict[str, str] = Field(default_factory=dict)


class ResourceMonitoring(BaseModel):
    """Monitoring configuration for a resource."""
    metrics: List[str] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    logs_enabled: bool = True
    monitoring_interval: int = 60  # seconds
    retention_days: int = 30


class Resource(BaseModel):
    """Cloud resource representation."""
    id: str
    name: str
    provider: CloudProvider
    type: ResourceType
    region: str
    status: ResourceStatus
    lifecycle: ResourceLifecycle
    criticality: ResourceCriticality
    tags: Dict[str, ResourceTag] = Field(default_factory=dict)
    metadata: ResourceMetadata
    dependencies: List[ResourceDependency] = Field(default_factory=list)
    compliance: Optional[ResourceCompliance] = None
    cost: Optional[ResourceCost] = None
    configuration: ResourceConfiguration
    permissions: List[ResourcePermission] = Field(default_factory=list)
    audit_logs: List[ResourceAuditLog] = Field(default_factory=list)
    backups: List[ResourceBackup] = Field(default_factory=list)
    monitoring: ResourceMonitoring
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True


class ResourceGroup(BaseModel):
    """Group of related resources."""
    id: str
    name: str
    description: Optional[str] = None
    resources: Set[str] = Field(default_factory=set)  # Set of resource IDs
    tags: Dict[str, ResourceTag] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResourceQuery(BaseModel):
    """Query parameters for resource search."""
    providers: Optional[List[CloudProvider]] = None
    types: Optional[List[ResourceType]] = None
    regions: Optional[List[str]] = None
    statuses: Optional[List[ResourceStatus]] = None
    lifecycles: Optional[List[ResourceLifecycle]] = None
    criticalities: Optional[List[ResourceCriticality]] = None
    tags: Optional[Dict[str, str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None


class ResourceSummary(BaseModel):
    """Summary of resources in inventory."""
    total_resources: int
    resources_by_provider: Dict[CloudProvider, int] = Field(default_factory=dict)
    resources_by_type: Dict[ResourceType, int] = Field(default_factory=dict)
    resources_by_status: Dict[ResourceStatus, int] = Field(default_factory=dict)
    resources_by_lifecycle: Dict[ResourceLifecycle, int] = Field(default_factory=dict)
    resources_by_criticality: Dict[ResourceCriticality, int] = Field(default_factory=dict)
    total_cost: Dict[str, float] = Field(default_factory=dict)  # By currency
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ResourceInventoryState(BaseModel):
    """Current state of the resource inventory."""
    resources: Dict[str, Resource]  # Resource ID -> Resource
    groups: Dict[str, ResourceGroup]  # Group ID -> ResourceGroup
    summary: ResourceSummary
    last_updated: datetime = Field(default_factory=datetime.utcnow)
