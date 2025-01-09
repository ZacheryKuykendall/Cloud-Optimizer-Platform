"""Custom exceptions for cloud compliance management.

This module defines exceptions specific to compliance management operations,
rule checking, and remediation actions.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID


class CloudComplianceError(Exception):
    """Base exception for all cloud compliance errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ComplianceRuleError(CloudComplianceError):
    """Base class for compliance rule-related errors."""

    def __init__(
        self,
        message: str,
        rule_id: Optional[UUID] = None,
        framework: Optional[str] = None
    ):
        super().__init__(message)
        self.rule_id = rule_id
        self.framework = framework


class RuleNotFoundError(ComplianceRuleError):
    """Raised when a compliance rule cannot be found."""
    pass


class RuleValidationError(ComplianceRuleError):
    """Raised when rule validation fails."""

    def __init__(
        self,
        message: str,
        rule_id: Optional[UUID] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(message, rule_id)
        self.field = field
        self.value = value


class ComplianceCheckError(CloudComplianceError):
    """Raised when there are issues with compliance checks."""

    def __init__(
        self,
        message: str,
        check_id: UUID,
        resource_id: str,
        rule_id: UUID,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.check_id = check_id
        self.resource_id = resource_id
        self.rule_id = rule_id
        self.details = details or {}


class RemediationError(CloudComplianceError):
    """Raised when there are issues with remediation actions."""

    def __init__(
        self,
        message: str,
        violation_id: UUID,
        action_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.violation_id = violation_id
        self.action_type = action_type
        self.details = details or {}


class FrameworkError(CloudComplianceError):
    """Raised when there are issues with compliance frameworks."""

    def __init__(
        self,
        message: str,
        framework: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.framework = framework
        self.operation = operation
        self.details = details or {}


class MonitorError(CloudComplianceError):
    """Raised when there are issues with compliance monitoring."""

    def __init__(
        self,
        message: str,
        monitor_id: UUID,
        resource_types: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.monitor_id = monitor_id
        self.resource_types = resource_types
        self.details = details or {}


class ReportError(CloudComplianceError):
    """Raised when there are issues with compliance reporting."""

    def __init__(
        self,
        message: str,
        report_id: UUID,
        framework: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.report_id = report_id
        self.framework = framework
        self.details = details or {}


class AuditError(CloudComplianceError):
    """Raised when there are issues with compliance audits."""

    def __init__(
        self,
        message: str,
        audit_id: UUID,
        framework: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.audit_id = audit_id
        self.framework = framework
        self.status = status
        self.details = details or {}


class PolicyError(CloudComplianceError):
    """Raised when there are issues with compliance policies."""

    def __init__(
        self,
        message: str,
        policy_id: UUID,
        scope: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.policy_id = policy_id
        self.scope = scope
        self.details = details or {}


class ExceptionError(CloudComplianceError):
    """Raised when there are issues with compliance exceptions."""

    def __init__(
        self,
        message: str,
        exception_id: UUID,
        rule_id: UUID,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.exception_id = exception_id
        self.rule_id = rule_id
        self.resource_id = resource_id
        self.details = details or {}


class EvidenceError(CloudComplianceError):
    """Raised when there are issues with compliance evidence."""

    def __init__(
        self,
        message: str,
        evidence_id: UUID,
        check_id: UUID,
        evidence_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.evidence_id = evidence_id
        self.check_id = check_id
        self.evidence_type = evidence_type
        self.details = details or {}


class NotificationError(CloudComplianceError):
    """Raised when there are issues with compliance notifications."""

    def __init__(
        self,
        message: str,
        notification_id: UUID,
        notification_type: str,
        recipients: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.notification_id = notification_id
        self.notification_type = notification_type
        self.recipients = recipients
        self.details = details or {}


class ProviderError(CloudComplianceError):
    """Raised when there are issues with cloud provider APIs."""

    def __init__(
        self,
        message: str,
        provider: str,
        service: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.service = service
        self.operation = operation
        self.details = details or {}


class MetricsError(CloudComplianceError):
    """Raised when there are issues with compliance metrics."""

    def __init__(
        self,
        message: str,
        framework: str,
        metric_type: str,
        period: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.framework = framework
        self.metric_type = metric_type
        self.period = period
        self.details = details or {}


class ConfigurationError(CloudComplianceError):
    """Raised when there are issues with compliance configuration."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.config_key = config_key
        self.config_value = config_value
        self.details = details or {}
