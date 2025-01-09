"""Cloud Governance Manager

A Python library for managing cloud governance policies and controls across different providers.
This library provides functionality for policy management, access control,
and governance monitoring.
"""

from cloud_governance_manager.models import (
    PolicyType,
    PolicyScope,
    PolicyEffect,
    ControlType,
    AccessLevel,
    PolicyCondition,
    PolicyAction,
    Policy,
    RolePermission,
    Role,
    ResourceControl,
    AccessReview,
    PolicyEvaluation,
    GovernanceEvent,
    GovernanceMetrics,
    OrganizationalUnit,
    PolicySet,
    GovernanceReport,
    PolicyTemplate,
    GovernanceConfiguration,
)
from cloud_governance_manager.exceptions import (
    CloudGovernanceError,
    PolicyError,
    PolicyNotFoundError,
    PolicyValidationError,
    PolicyEvaluationError,
    RoleError,
    AccessControlError,
    ResourceControlError,
    AccessReviewError,
    OrganizationError,
    PolicySetError,
    GovernanceEventError,
    MetricsError,
    ReportError,
    TemplateError,
    ConfigurationError,
    ProviderError,
)

__version__ = "0.1.0"

__all__ = [
    # Enums
    "PolicyType",
    "PolicyScope",
    "PolicyEffect",
    "ControlType",
    "AccessLevel",

    # Core Models
    "PolicyCondition",
    "PolicyAction",
    "Policy",
    "RolePermission",
    "Role",
    "ResourceControl",
    "AccessReview",
    "PolicyEvaluation",
    "GovernanceEvent",
    "GovernanceMetrics",
    "OrganizationalUnit",
    "PolicySet",
    "GovernanceReport",
    "PolicyTemplate",
    "GovernanceConfiguration",

    # Base Exceptions
    "CloudGovernanceError",
    "PolicyError",
    "PolicyNotFoundError",
    "PolicyValidationError",
    "PolicyEvaluationError",

    # Feature-specific Exceptions
    "RoleError",
    "AccessControlError",
    "ResourceControlError",
    "AccessReviewError",
    "OrganizationError",
    "PolicySetError",
    "GovernanceEventError",
    "MetricsError",
    "ReportError",
    "TemplateError",

    # System Exceptions
    "ConfigurationError",
    "ProviderError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
