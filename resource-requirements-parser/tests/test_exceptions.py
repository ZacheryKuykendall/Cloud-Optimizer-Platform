"""Tests for custom exceptions."""

import pytest

from resource_requirements_parser.exceptions import (
    ResourceRequirementsError,
    ParsingError,
    ValidationError,
    UnsupportedSourceError,
    ResourceTypeError,
    DependencyError,
    CircularDependencyError,
    RequirementsMissingError,
    RequirementsConflictError,
    FileAccessError,
    TemplateFormatError,
    VariableResolutionError,
    ModuleResolutionError,
    ResourceLimitError,
)


def test_base_exception():
    """Test base ResourceRequirementsError."""
    # Test basic error
    error = ResourceRequirementsError("Test error")
    assert str(error) == "Test error"
    assert error.message == "Test error"
    assert error.details == {}

    # Test with details
    error = ResourceRequirementsError(
        "Test error",
        details={"key": "value"}
    )
    assert error.details["key"] == "value"


def test_parsing_error():
    """Test ParsingError."""
    error = ParsingError(
        message="Failed to parse file",
        source_type="terraform",
        source_path="/path/to/file",
        line_number=10,
        column=5,
        details={"error_type": "syntax"}
    )
    assert error.message == "Failed to parse file"
    assert error.source_type == "terraform"
    assert error.source_path == "/path/to/file"
    assert error.line_number == 10
    assert error.column == 5
    assert error.details["error_type"] == "syntax"


def test_validation_error():
    """Test ValidationError."""
    error = ValidationError(
        message="Invalid value",
        resource_name="web_server",
        field="instance_type",
        value="invalid_type",
        details={"valid_types": ["t2.micro", "t2.small"]}
    )
    assert error.message == "Invalid value"
    assert error.resource_name == "web_server"
    assert error.field == "instance_type"
    assert error.value == "invalid_type"
    assert "valid_types" in error.details


def test_unsupported_source_error():
    """Test UnsupportedSourceError."""
    error = UnsupportedSourceError(
        message="Unsupported source type",
        source_type="unknown",
        supported_types=["terraform", "cloudformation"],
        details={"suggestion": "Use terraform instead"}
    )
    assert error.message == "Unsupported source type"
    assert error.source_type == "unknown"
    assert "terraform" in error.supported_types
    assert error.details["suggestion"] == "Use terraform instead"


def test_resource_type_error():
    """Test ResourceTypeError."""
    error = ResourceTypeError(
        message="Unknown resource type",
        resource_name="custom_resource",
        resource_type="unknown_type",
        details={"valid_types": ["compute", "storage"]}
    )
    assert error.message == "Unknown resource type"
    assert error.resource_name == "custom_resource"
    assert error.resource_type == "unknown_type"
    assert "valid_types" in error.details


def test_dependency_error():
    """Test DependencyError."""
    error = DependencyError(
        message="Missing dependency",
        resource_name="web_server",
        dependency_name="vpc",
        details={"required": True}
    )
    assert error.message == "Missing dependency"
    assert error.resource_name == "web_server"
    assert error.dependency_name == "vpc"
    assert error.details["required"] is True


def test_circular_dependency_error():
    """Test CircularDependencyError."""
    error = CircularDependencyError(
        message="Circular dependency detected",
        resource_name="a",
        dependency_name="c",
        dependency_chain=["a", "b", "c", "a"],
        details={"cycle_length": 3}
    )
    assert error.message == "Circular dependency detected"
    assert error.resource_name == "a"
    assert error.dependency_name == "c"
    assert error.dependency_chain == ["a", "b", "c", "a"]
    assert error.details["cycle_length"] == 3


def test_requirements_missing_error():
    """Test RequirementsMissingError."""
    error = RequirementsMissingError(
        message="Missing required fields",
        resource_name="database",
        missing_fields=["engine", "version"],
        details={"severity": "error"}
    )
    assert error.message == "Missing required fields"
    assert error.resource_name == "database"
    assert "engine" in error.missing_fields
    assert "version" in error.missing_fields
    assert error.details["severity"] == "error"


def test_requirements_conflict_error():
    """Test RequirementsConflictError."""
    error = RequirementsConflictError(
        message="Conflicting requirements",
        resource_name="instance",
        conflicting_fields={
            "instance_type": ["t2.micro", "t2.large"],
            "region": ["us-east-1", "us-west-2"]
        },
        details={"resolution": "Choose one instance type"}
    )
    assert error.message == "Conflicting requirements"
    assert error.resource_name == "instance"
    assert len(error.conflicting_fields) == 2
    assert error.details["resolution"] == "Choose one instance type"


def test_file_access_error():
    """Test FileAccessError."""
    error = FileAccessError(
        message="Cannot read file",
        file_path="/path/to/file",
        operation="read",
        details={"error_code": "ENOENT"}
    )
    assert error.message == "Cannot read file"
    assert error.file_path == "/path/to/file"
    assert error.operation == "read"
    assert error.details["error_code"] == "ENOENT"


def test_template_format_error():
    """Test TemplateFormatError."""
    error = TemplateFormatError(
        message="Invalid template format",
        source_type="cloudformation",
        template_version="invalid-version",
        details={"valid_versions": ["2010-09-09"]}
    )
    assert error.message == "Invalid template format"
    assert error.source_type == "cloudformation"
    assert error.template_version == "invalid-version"
    assert "valid_versions" in error.details


def test_variable_resolution_error():
    """Test VariableResolutionError."""
    error = VariableResolutionError(
        message="Cannot resolve variable",
        variable_name="environment",
        source_type="terraform",
        resource_name="web_server",
        details={"required": True}
    )
    assert error.message == "Cannot resolve variable"
    assert error.variable_name == "environment"
    assert error.source_type == "terraform"
    assert error.resource_name == "web_server"
    assert error.details["required"] is True


def test_module_resolution_error():
    """Test ModuleResolutionError."""
    error = ModuleResolutionError(
        message="Cannot resolve module",
        module_name="vpc",
        source_type="terraform",
        source_path="modules/vpc",
        details={"source": "git://example.com/vpc"}
    )
    assert error.message == "Cannot resolve module"
    assert error.module_name == "vpc"
    assert error.source_type == "terraform"
    assert error.source_path == "modules/vpc"
    assert error.details["source"] == "git://example.com/vpc"


def test_resource_limit_error():
    """Test ResourceLimitError."""
    error = ResourceLimitError(
        message="Resource limit exceeded",
        resource_name="ec2_instances",
        limit_type="count",
        current_value=11,
        limit_value=10,
        details={"region": "us-west-2"}
    )
    assert error.message == "Resource limit exceeded"
    assert error.resource_name == "ec2_instances"
    assert error.limit_type == "count"
    assert error.current_value == 11
    assert error.limit_value == 10
    assert error.details["region"] == "us-west-2"


def test_exception_inheritance():
    """Test exception inheritance relationships."""
    # All exceptions should inherit from ResourceRequirementsError
    exceptions = [
        ParsingError("test", "type", "path"),
        ValidationError("test"),
        UnsupportedSourceError("test", "type", []),
        ResourceTypeError("test", "name", "type"),
        DependencyError("test", "res", "dep"),
        CircularDependencyError("test", "res", "dep", []),
        RequirementsMissingError("test", "res", []),
        RequirementsConflictError("test", "res", {}),
        FileAccessError("test", "path", "read"),
        TemplateFormatError("test", "type"),
        VariableResolutionError("test", "var", "type"),
        ModuleResolutionError("test", "module", "type", "path"),
        ResourceLimitError("test", "res", "limit", 1, 0),
    ]

    for error in exceptions:
        assert isinstance(error, ResourceRequirementsError)
        assert isinstance(error, Exception)
