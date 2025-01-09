"""Exceptions for Resource Requirements Parser.

This module defines custom exceptions for handling various error scenarios
that may occur during parsing of infrastructure requirements.
"""

from typing import Any, Dict, List, Optional


class ResourceRequirementsError(Exception):
    """Base exception for all resource requirements parser errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ParsingError(ResourceRequirementsError):
    """Raised when there is an error parsing the infrastructure definition."""

    def __init__(
        self,
        message: str,
        source_type: str,
        source_path: str,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.source_type = source_type
        self.source_path = source_path
        self.line_number = line_number
        self.column = column


class ValidationError(ResourceRequirementsError):
    """Raised when parsed requirements fail validation."""

    def __init__(
        self,
        message: str,
        resource_name: Optional[str] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.resource_name = resource_name
        self.field = field
        self.value = value


class UnsupportedSourceError(ResourceRequirementsError):
    """Raised when the infrastructure definition source type is not supported."""

    def __init__(
        self,
        message: str,
        source_type: str,
        supported_types: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.source_type = source_type
        self.supported_types = supported_types


class ResourceTypeError(ResourceRequirementsError):
    """Raised when there is an error with resource type identification."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        resource_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.resource_name = resource_name
        self.resource_type = resource_type


class DependencyError(ResourceRequirementsError):
    """Raised when there are issues with resource dependencies."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        dependency_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.resource_name = resource_name
        self.dependency_name = dependency_name


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected between resources."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        dependency_name: str,
        dependency_chain: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, resource_name, dependency_name, details)
        self.dependency_chain = dependency_chain


class RequirementsMissingError(ResourceRequirementsError):
    """Raised when required resource requirements are missing."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        missing_fields: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.resource_name = resource_name
        self.missing_fields = missing_fields


class RequirementsConflictError(ResourceRequirementsError):
    """Raised when there are conflicting requirements for a resource."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        conflicting_fields: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.resource_name = resource_name
        self.conflicting_fields = conflicting_fields


class FileAccessError(ResourceRequirementsError):
    """Raised when there are issues accessing infrastructure definition files."""

    def __init__(
        self,
        message: str,
        file_path: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.file_path = file_path
        self.operation = operation


class TemplateFormatError(ResourceRequirementsError):
    """Raised when there are issues with the infrastructure template format."""

    def __init__(
        self,
        message: str,
        source_type: str,
        template_version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.source_type = source_type
        self.template_version = template_version


class VariableResolutionError(ResourceRequirementsError):
    """Raised when there are issues resolving variables in templates."""

    def __init__(
        self,
        message: str,
        variable_name: str,
        source_type: str,
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.variable_name = variable_name
        self.source_type = source_type
        self.resource_name = resource_name


class ModuleResolutionError(ResourceRequirementsError):
    """Raised when there are issues resolving external modules or imports."""

    def __init__(
        self,
        message: str,
        module_name: str,
        source_type: str,
        source_path: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.module_name = module_name
        self.source_type = source_type
        self.source_path = source_path


class ResourceLimitError(ResourceRequirementsError):
    """Raised when resource requirements exceed defined limits."""

    def __init__(
        self,
        message: str,
        resource_name: str,
        limit_type: str,
        current_value: Any,
        limit_value: Any,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.resource_name = resource_name
        self.limit_type = limit_type
        self.current_value = current_value
        self.limit_value = limit_value
