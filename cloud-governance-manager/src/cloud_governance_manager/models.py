"""Data models for cloud governance management.

This module provides data models for representing policies, controls,
and governance across different cloud providers.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class PolicyType(str, Enum):
    """Types of governance policies."""
    ACCESS_CONTROL = "access_control"
    RESOURCE = "resource"
    COST = "cost"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class PolicyScope(str, Enum):
    """Scopes for policy application."""
    ORGANIZATION = "organization"
    ACCOUNT = "account"
    PROJECT = "project"
    RESOURCE_GROUP = "resource_group"
    RESOURCE = "resource"


class PolicyEffect(str, Enum):
    """Effects of policy evaluation."""
    ALLOW = "allow"
    DENY = "deny"
    AUDIT = "audit"
    REMEDIATE = "remediate"


class ControlType(str, Enum):
    """Types of governance controls."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"
    DIRECTIVE = "directive"


class AccessLevel(str, Enum):
    """Access levels for permissions."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    CUSTOM = "custom"


class PolicyCondition(BaseModel):
    """Model for policy conditions."""
    field: str
    operator: str  # equals, not_equals, contains, etc.
    value: Any
    negate: bool = False
    case_sensitive: bool = True


class PolicyAction(BaseModel):
    """Model for policy actions."""
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    provider_specific: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class Policy(BaseModel):
    """Model for governance policies."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    type: PolicyType
    scope: PolicyScope
    effect: PolicyEffect
    conditions: List[PolicyCondition] = Field(default_factory=list)
    actions: List[PolicyAction] = Field(default_factory=list)
    priority: int = 0
    version: str = "1.0.0"
    enabled: bool = True
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RolePermission(BaseModel):
    """Model for role permissions."""
    resource_type: str
    access_level: AccessLevel
    conditions: List[PolicyCondition] = Field(default_factory=list)
    provider_specific: Dict[str, Any] = Field(default_factory=dict)


class Role(BaseModel):
    """Model for governance roles."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    permissions: List[RolePermission] = Field(default_factory=list)
    scope: PolicyScope
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResourceControl(BaseModel):
    """Model for resource controls."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: ControlType
    resource_types: List[str]
    policies: List[UUID] = Field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AccessReview(BaseModel):
    """Model for access reviews."""
    id: UUID = Field(default_factory=uuid4)
    reviewer: str
    subject: str  # user, role, or group being reviewed
    scope: PolicyScope
    status: str  # pending, approved, rejected
    decision: Optional[str] = None
    justification: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluation(BaseModel):
    """Model for policy evaluation results."""
    id: UUID = Field(default_factory=uuid4)
    policy_id: UUID
    resource_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    effect: PolicyEffect
    matched_conditions: List[PolicyCondition] = Field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceEvent(BaseModel):
    """Model for governance-related events."""
    id: UUID = Field(default_factory=uuid4)
    event_type: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
    user: Optional[str] = None
    resource_id: Optional[str] = None


class GovernanceMetrics(BaseModel):
    """Model for governance metrics."""
    policy_evaluations: int
    policy_violations: int
    access_reviews_pending: int
    access_reviews_completed: int
    resources_controlled: int
    active_policies: int
    active_controls: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OrganizationalUnit(BaseModel):
    """Model for organizational units."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    parent_id: Optional[UUID] = None
    policies: List[UUID] = Field(default_factory=list)
    roles: List[UUID] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicySet(BaseModel):
    """Model for policy sets."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    policies: List[UUID] = Field(default_factory=list)
    scope: PolicyScope
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceReport(BaseModel):
    """Model for governance reports."""
    id: UUID = Field(default_factory=uuid4)
    report_type: str
    period_start: datetime
    period_end: datetime
    metrics: GovernanceMetrics
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyTemplate(BaseModel):
    """Model for policy templates."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    policy_type: PolicyType
    template: Dict[str, Any]
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceConfiguration(BaseModel):
    """Model for governance configuration."""
    organization_id: str
    default_policies: List[UUID] = Field(default_factory=list)
    default_roles: List[UUID] = Field(default_factory=list)
    review_frequency_days: int = 90
    metrics_retention_days: int = 365
    enabled_controls: List[str] = Field(default_factory=list)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)
