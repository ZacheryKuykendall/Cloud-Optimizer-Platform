"""Models for Resource Requirements Parser.

This module defines data models for representing infrastructure requirements
parsed from various sources like Terraform, CloudFormation, etc.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class ResourceType(str, Enum):
    """Types of cloud resources."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CONTAINER = "container"
    SERVERLESS = "serverless"
    CACHE = "cache"
    QUEUE = "queue"
    LOAD_BALANCER = "load_balancer"
    DNS = "dns"
    CDN = "cdn"
    MONITORING = "monitoring"
    SECURITY = "security"
    IAM = "iam"
    OTHER = "other"


class ComputeType(str, Enum):
    """Types of compute resources."""
    VM = "vm"
    CONTAINER = "container"
    FUNCTION = "function"
    KUBERNETES = "kubernetes"


class StorageType(str, Enum):
    """Types of storage resources."""
    BLOCK = "block"
    OBJECT = "object"
    FILE = "file"
    ARCHIVE = "archive"


class NetworkType(str, Enum):
    """Types of network resources."""
    VPC = "vpc"
    SUBNET = "subnet"
    ROUTE_TABLE = "route_table"
    SECURITY_GROUP = "security_group"
    LOAD_BALANCER = "load_balancer"
    VPN = "vpn"
    FIREWALL = "firewall"


class DatabaseType(str, Enum):
    """Types of database resources."""
    RELATIONAL = "relational"
    NOSQL = "nosql"
    GRAPH = "graph"
    TIMESERIES = "timeseries"
    CACHE = "cache"


class SourceType(str, Enum):
    """Types of infrastructure definition sources."""
    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    ARM_TEMPLATE = "arm_template"
    KUBERNETES = "kubernetes"
    CUSTOM = "custom"


class ComputeRequirements(BaseModel):
    """Requirements for compute resources."""
    type: ComputeType
    vcpus: int
    memory_gb: float
    gpu_count: Optional[int] = None
    gpu_type: Optional[str] = None
    architecture: Optional[str] = None
    operating_system: Optional[str] = None
    instance_count: int = 1
    availability_zones: Optional[List[str]] = None
    custom_requirements: Dict[str, Any] = Field(default_factory=dict)


class StorageRequirements(BaseModel):
    """Requirements for storage resources."""
    type: StorageType
    capacity_gb: float
    iops: Optional[int] = None
    throughput_mbps: Optional[float] = None
    encryption_required: bool = False
    backup_required: bool = False
    replication_required: bool = False
    custom_requirements: Dict[str, Any] = Field(default_factory=dict)


class NetworkRequirements(BaseModel):
    """Requirements for network resources."""
    type: NetworkType
    cidr_block: Optional[str] = None
    port_ranges: Optional[List[Dict[str, int]]] = None
    protocols: Optional[List[str]] = None
    public_access: bool = False
    vpn_required: bool = False
    custom_requirements: Dict[str, Any] = Field(default_factory=dict)


class DatabaseRequirements(BaseModel):
    """Requirements for database resources."""
    type: DatabaseType
    engine: str
    version: str
    storage_gb: float
    multi_az: bool = False
    backup_retention_days: Optional[int] = None
    encryption_required: bool = True
    custom_requirements: Dict[str, Any] = Field(default_factory=dict)


class ResourceRequirements(BaseModel):
    """Requirements for a specific cloud resource."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: ResourceType
    compute: Optional[ComputeRequirements] = None
    storage: Optional[StorageRequirements] = None
    network: Optional[NetworkRequirements] = None
    database: Optional[DatabaseRequirements] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    custom_requirements: Dict[str, Any] = Field(default_factory=dict)

    @validator("compute")
    def validate_compute(cls, v, values):
        """Validate compute requirements."""
        if values.get("type") == ResourceType.COMPUTE and not v:
            raise ValueError("Compute requirements are required for compute resources")
        return v

    @validator("storage")
    def validate_storage(cls, v, values):
        """Validate storage requirements."""
        if values.get("type") == ResourceType.STORAGE and not v:
            raise ValueError("Storage requirements are required for storage resources")
        return v

    @validator("network")
    def validate_network(cls, v, values):
        """Validate network requirements."""
        if values.get("type") == ResourceType.NETWORK and not v:
            raise ValueError("Network requirements are required for network resources")
        return v

    @validator("database")
    def validate_database(cls, v, values):
        """Validate database requirements."""
        if values.get("type") == ResourceType.DATABASE and not v:
            raise ValueError("Database requirements are required for database resources")
        return v


class InfrastructureRequirements(BaseModel):
    """Complete infrastructure requirements parsed from a source."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    source_type: SourceType
    source_path: str
    resources: List[ResourceRequirements]
    global_tags: Dict[str, str] = Field(default_factory=dict)
    creation_time: datetime = Field(default_factory=datetime.utcnow)
    last_modified_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_resource_by_name(self, name: str) -> Optional[ResourceRequirements]:
        """Get a resource by its name."""
        for resource in self.resources:
            if resource.name == name:
                return resource
        return None

    def get_resources_by_type(self, type: ResourceType) -> List[ResourceRequirements]:
        """Get all resources of a specific type."""
        return [r for r in self.resources if r.type == type]

    def get_dependent_resources(self, resource_name: str) -> List[ResourceRequirements]:
        """Get all resources that depend on the specified resource."""
        return [r for r in self.resources if resource_name in r.dependencies]

    def get_dependencies(self, resource_name: str) -> List[ResourceRequirements]:
        """Get all resources that the specified resource depends on."""
        resource = self.get_resource_by_name(resource_name)
        if not resource:
            return []
        return [r for r in self.resources if r.name in resource.dependencies]


class ParsingResult(BaseModel):
    """Result of parsing infrastructure requirements."""
    requirements: InfrastructureRequirements
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
