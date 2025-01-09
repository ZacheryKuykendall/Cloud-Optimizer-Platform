"""Cloud Compliance Manager

A Python library for managing and monitoring cloud compliance across different providers.
This library provides functionality for compliance frameworks, rules, monitoring,
and remediation actions.
"""

from cloud_compliance_manager.models import (
    ComplianceFramework,
    ComplianceLevel,
    ResourceType,
    ComplianceStatus,
    RiskLevel,
    RemediationType,
    ComplianceRule,
    ComplianceCheck,
    ComplianceViolation,
    ComplianceReport,
    ComplianceMonitor,
    RemediationAction,
    ComplianceEvidence,
    ComplianceAudit,
    CompliancePolicy,
    ComplianceException,
    ComplianceMetrics,
    ComplianceNotification,
)
from cloud_compliance_manager.exceptions import (
    CloudComplianceError,
    ComplianceRuleError,
    RuleNotFoundError,
    RuleValidationError,
    ComplianceCheckError,
    RemediationError,
    FrameworkError,
    MonitorError,
    ReportError,
    AuditError,
    PolicyError,
    ExceptionError,
    EvidenceError,
    NotificationError,
    ProviderError,
    MetricsError,
    ConfigurationError,
)

__version__ = "0.1.0"

__all__ = [
    # Enums
    "ComplianceFramework",
    "ComplianceLevel",
    "ResourceType",
    "ComplianceStatus",
    "RiskLevel",
    "RemediationType",

    # Core Models
    "ComplianceRule",
    "ComplianceCheck",
    "ComplianceViolation",
    "ComplianceReport",
    "ComplianceMonitor",
    "RemediationAction",
    "ComplianceEvidence",
    "ComplianceAudit",
    "CompliancePolicy",
    "ComplianceException",
    "ComplianceMetrics",
    "ComplianceNotification",

    # Base Exceptions
    "CloudComplianceError",
    "ComplianceRuleError",
    "RuleNotFoundError",
    "RuleValidationError",

    # Feature-specific Exceptions
    "ComplianceCheckError",
    "RemediationError",
    "FrameworkError",
    "MonitorError",
    "ReportError",
    "AuditError",
    "PolicyError",
    "ExceptionError",
    "EvidenceError",
    "NotificationError",

    # System Exceptions
    "ProviderError",
    "MetricsError",
    "ConfigurationError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
