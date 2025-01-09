"""Data models for cloud compliance management.

This module provides data models for representing compliance frameworks,
rules, and monitoring across different cloud providers.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    CIS = "cis"
    HIPAA = "hipaa"
    PCI = "pci"
    SOC2 = "soc2"
    NIST = "nist"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    CUSTOM = "custom"


class ComplianceLevel(str, Enum):
    """Compliance requirement levels."""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class ResourceType(str, Enum):
    """Types of cloud resources to check."""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    SECURITY = "security"
    IDENTITY = "identity"
    MONITORING = "monitoring"
    OTHER = "other"


class ComplianceStatus(str, Enum):
    """Status of compliance checks."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Risk levels for compliance issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RemediationType(str, Enum):
    """Types of remediation actions."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    HYBRID = "hybrid"


class ComplianceRule(BaseModel):
    """Model for compliance rules."""
    id: UUID = Field(default_factory=uuid4)
    framework: ComplianceFramework
    rule_id: str
    title: str
    description: str
    level: ComplianceLevel
    resource_type: ResourceType
    provider_specific: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    tags: Dict[str, str] = Field(default_factory=dict)


class ComplianceCheck(BaseModel):
    """Model for compliance check results."""
    id: UUID = Field(default_factory=uuid4)
    rule_id: UUID
    resource_id: str
    status: ComplianceStatus
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence: Optional[str] = None


class ComplianceViolation(BaseModel):
    """Model for compliance violations."""
    id: UUID = Field(default_factory=uuid4)
    check_id: UUID
    risk_level: RiskLevel
    description: str
    remediation_steps: List[str]
    remediation_type: RemediationType
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "open"  # open, in_progress, resolved, ignored
    resolution_notes: Optional[str] = None


class ComplianceReport(BaseModel):
    """Model for compliance reports."""
    id: UUID = Field(default_factory=uuid4)
    framework: ComplianceFramework
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_rules: int
    compliant_rules: int
    non_compliant_rules: int
    not_applicable_rules: int
    error_rules: int
    violations_by_risk: Dict[RiskLevel, int]
    violations_by_resource: Dict[ResourceType, int]
    details: Dict[str, Any] = Field(default_factory=dict)


class ComplianceMonitor(BaseModel):
    """Model for compliance monitoring configuration."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    frameworks: List[ComplianceFramework]
    resource_types: List[ResourceType]
    schedule: str  # cron expression
    enabled: bool = True
    notification_config: Dict[str, Any] = Field(default_factory=dict)
    last_run: Optional[datetime] = None


class RemediationAction(BaseModel):
    """Model for remediation actions."""
    id: UUID = Field(default_factory=uuid4)
    violation_id: UUID
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    automated: bool = False
    approval_required: bool = True
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, approved, rejected, executed, failed


class ComplianceEvidence(BaseModel):
    """Model for compliance evidence."""
    id: UUID = Field(default_factory=uuid4)
    check_id: UUID
    type: str  # screenshot, log, config, other
    content: str
    format: str  # text, json, image, pdf
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComplianceAudit(BaseModel):
    """Model for compliance audits."""
    id: UUID = Field(default_factory=uuid4)
    framework: ComplianceFramework
    start_date: datetime
    end_date: Optional[datetime] = None
    auditor: str
    status: str  # planned, in_progress, completed, cancelled
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_ids: List[UUID] = Field(default_factory=list)
    notes: Optional[str] = None


class CompliancePolicy(BaseModel):
    """Model for compliance policies."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    frameworks: List[ComplianceFramework]
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    scope: str  # organization, account, project
    priority: int = 0
    enabled: bool = True


class ComplianceException(BaseModel):
    """Model for compliance exceptions."""
    id: UUID = Field(default_factory=uuid4)
    rule_id: UUID
    resource_id: str
    reason: str
    approved_by: str
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    documentation: Optional[str] = None
    status: str = "active"  # active, expired, revoked


class ComplianceMetrics(BaseModel):
    """Model for compliance metrics."""
    framework: ComplianceFramework
    period_start: datetime
    period_end: datetime
    compliance_score: float
    total_resources: int
    compliant_resources: int
    violations_count: int
    remediation_rate: float
    average_time_to_remediate: Optional[float] = None
    risk_score: float
    trend: Dict[str, float] = Field(default_factory=dict)


class ComplianceNotification(BaseModel):
    """Model for compliance notifications."""
    id: UUID = Field(default_factory=uuid4)
    type: str  # violation, audit, exception, other
    severity: str  # critical, high, medium, low, info
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    recipients: List[str]
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
