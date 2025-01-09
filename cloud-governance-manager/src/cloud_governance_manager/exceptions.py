"""Custom exceptions for cloud governance management.

This module defines exceptions specific to governance management operations,
policy enforcement, and access control.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID


class CloudGovernanceError(Exception):
    """Base exception for all cloud governance errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class PolicyError(CloudGovernanceError):
    """Base class for policy-related errors."""

    def __init__(
        self,
        message: str,
        policy_id: Optional[UUID] = None,
        policy_type: Optional[str] = None
    ):
        super().__init__(message)
        self.policy_id = policy_id
        self.policy_type = policy_type


class PolicyNotFoundError(PolicyError):
    """Raised when a policy cannot be found."""
    pass


class PolicyValidationError(PolicyError):
    """Raised when policy validation fails."""

    def __init__(
        self,
        message: str,
        policy_id: Optional[UUID] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(message, policy_id)
        self.field = field
        self.value = value


class PolicyEvaluationError(PolicyError):
    """Raised when there are issues with policy evaluation."""

    def __init__(
        self,
        message: str,
        policy_id: UUID,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, policy_id)
        self.resource_id = resource_id
        self.details = details or {}


class RoleError(CloudGovernanceError):
    """Raised when there are issues with roles."""

    def __init__(
        self,
        message: str,
        role_id: UUID,
        scope: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.role_id = role_id
        self.scope = scope
        self.details = details or {}


class AccessControlError(CloudGovernanceError):
    """Raised when there are access control issues."""

    def __init__(
        self,
        message: str,
        principal: str,
        resource: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.principal = principal
        self.resource = resource
        self.action = action
        self.details = details or {}


class ResourceControlError(CloudGovernanceError):
    """Raised when there are issues with resource controls."""

    def __init__(
        self,
        message: str,
        control_id: UUID,
        resource_types: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.control_id = control_id
        self.resource_types = resource_types
        self.details = details or {}


class AccessReviewError(CloudGovernanceError):
    """Raised when there are issues with access reviews."""

    def __init__(
        self,
        message: str,
        review_id: UUID,
        subject: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.review_id = review_id
        self.subject = subject
        self.status = status
        self.details = details or {}


class OrganizationError(CloudGovernanceError):
    """Raised when there are issues with organizational units."""

    def __init__(
        self,
        message: str,
        org_unit_id: UUID,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.org_unit_id = org_unit_id
        self.operation = operation
        self.details = details or {}


class PolicySetError(CloudGovernanceError):
    """Raised when there are issues with policy sets."""

    def __init__(
        self,
        message: str,
        policy_set_id: UUID,
        scope: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.policy_set_id = policy_set_id
        self.scope = scope
        self.details = details or {}


class GovernanceEventError(CloudGovernanceError):
    """Raised when there are issues with governance events."""

    def __init__(
        self,
        message: str,
        event_type: str,
        source: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.event_type = event_type
        self.source = source
        self.details = details or {}


class MetricsError(CloudGovernanceError):
    """Raised when there are issues with governance metrics."""

    def __init__(
        self,
        message: str,
        metric_type: str,
        period: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.metric_type = metric_type
        self.period = period
        self.details = details or {}


class ReportError(CloudGovernanceError):
    """Raised when there are issues with governance reports."""

    def __init__(
        self,
        message: str,
        report_id: UUID,
        report_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.report_id = report_id
        self.report_type = report_type
        self.details = details or {}


class TemplateError(CloudGovernanceError):
    """Raised when there are issues with policy templates."""

    def __init__(
        self,
        message: str,
        template_id: UUID,
        policy_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.template_id = template_id
        self.policy_type = policy_type
        self.details = details or {}


class ConfigurationError(CloudGovernanceError):
    """Raised when there are issues with governance configuration."""

    def __init__(
        self,
        message: str,
        organization_id: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.organization_id = organization_id
        self.config_key = config_key
        self.details = details or {}


class ProviderError(CloudGovernanceError):
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
