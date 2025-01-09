"""Resource Requirements Parser.

This module provides functionality for parsing infrastructure requirements
from various sources like Terraform, CloudFormation, etc.
"""

from resource_requirements_parser.models import (
    # Resource Types
    ResourceType,
    ComputeType,
    StorageType,
    NetworkType,
    DatabaseType,
    SourceType,

    # Resource Requirements
    ResourceRequirements,
    ComputeRequirements,
    StorageRequirements,
    NetworkRequirements,
    DatabaseRequirements,

    # Infrastructure Requirements
    InfrastructureRequirements,
    ParsingResult,
)

from resource_requirements_parser.exceptions import (
    # Base Exceptions
    ResourceRequirementsError,
    ParsingError,
    ValidationError,

    # Resource Errors
    ResourceTypeError,
    RequirementsMissingError,
    RequirementsConflictError,

    # Source Errors
    UnsupportedSourceError,
    FileAccessError,
    TemplateFormatError,

    # Variable Errors
    VariableResolutionError,
    ModuleResolutionError,
)

from resource_requirements_parser.parser import (
    BaseParser,
    ParserRegistry,
)

from resource_requirements_parser.parsers.terraform import TerraformParser
from resource_requirements_parser.parsers.cloudformation import CloudFormationParser

# Register parsers
ParserRegistry.register(SourceType.TERRAFORM, TerraformParser)
ParserRegistry.register(SourceType.CLOUDFORMATION, CloudFormationParser)

__version__ = "0.1.0"

__all__ = [
    # Resource Types
    "ResourceType",
    "ComputeType",
    "StorageType",
    "NetworkType",
    "DatabaseType",
    "SourceType",

    # Resource Requirements
    "ResourceRequirements",
    "ComputeRequirements",
    "StorageRequirements",
    "NetworkRequirements",
    "DatabaseRequirements",

    # Infrastructure Requirements
    "InfrastructureRequirements",
    "ParsingResult",

    # Base Exceptions
    "ResourceRequirementsError",
    "ParsingError",
    "ValidationError",

    # Resource Errors
    "ResourceTypeError",
    "RequirementsMissingError",
    "RequirementsConflictError",

    # Source Errors
    "UnsupportedSourceError",
    "FileAccessError",
    "TemplateFormatError",

    # Variable Errors
    "VariableResolutionError",
    "ModuleResolutionError",

    # Parser Classes
    "BaseParser",
    "ParserRegistry",
    "TerraformParser",
    "CloudFormationParser",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


def parse_requirements(source_path: str, source_type: SourceType) -> ParsingResult:
    """Parse infrastructure requirements from a source.

    This is the main entry point for parsing infrastructure requirements.
    It automatically selects the appropriate parser based on the source type.

    Args:
        source_path: Path to infrastructure definition file or directory
        source_type: Type of infrastructure definition source

    Returns:
        ParsingResult: The parsed requirements with any warnings/errors

    Raises:
        UnsupportedSourceError: If no parser is available for source type
        ParsingError: If there are errors parsing the source
        ValidationError: If parsed requirements fail validation
        FileAccessError: If there are issues accessing source files

    Example:
        >>> from resource_requirements_parser import parse_requirements, SourceType
        >>> result = parse_requirements("path/to/terraform", SourceType.TERRAFORM)
        >>> print(f"Found {len(result.requirements.resources)} resources")
        >>> for warning in result.warnings:
        ...     print(f"Warning: {warning}")
    """
    parser = ParserRegistry.get_parser(source_type, source_path)
    return parser.parse()


def get_supported_source_types() -> List[SourceType]:
    """Get list of supported infrastructure definition source types.

    Returns:
        List[SourceType]: List of source types that can be parsed

    Example:
        >>> from resource_requirements_parser import get_supported_source_types
        >>> supported_types = get_supported_source_types()
        >>> print("Supported source types:")
        >>> for source_type in supported_types:
        ...     print(f"- {source_type.value}")
    """
    return list(ParserRegistry.get_supported_types())
