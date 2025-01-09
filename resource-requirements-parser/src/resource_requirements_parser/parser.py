"""Base Parser for Resource Requirements.

This module defines the abstract base class and interfaces for parsing
infrastructure requirements from various source formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from resource_requirements_parser.models import (
    InfrastructureRequirements,
    ParsingResult,
    ResourceRequirements,
    ResourceType,
    SourceType,
)
from resource_requirements_parser.exceptions import (
    ParsingError,
    ValidationError,
    UnsupportedSourceError,
    ResourceTypeError,
    FileAccessError,
)


class BaseParser(ABC):
    """Abstract base class for infrastructure requirement parsers."""

    def __init__(self, source_path: Union[str, Path]):
        """Initialize parser.

        Args:
            source_path: Path to infrastructure definition file or directory
        """
        self.source_path = Path(source_path)
        self._validate_source()

    @abstractmethod
    def get_source_type(self) -> SourceType:
        """Get the type of infrastructure definition source this parser handles.

        Returns:
            SourceType: The source type (e.g., TERRAFORM, CLOUDFORMATION)
        """
        pass

    @abstractmethod
    def parse(self) -> ParsingResult:
        """Parse infrastructure requirements from the source.

        Returns:
            ParsingResult: The parsed requirements with any warnings/errors

        Raises:
            ParsingError: If there are errors parsing the source
            ValidationError: If parsed requirements fail validation
            FileAccessError: If there are issues accessing source files
        """
        pass

    @abstractmethod
    def validate(self, requirements: InfrastructureRequirements) -> List[str]:
        """Validate parsed infrastructure requirements.

        Args:
            requirements: The requirements to validate

        Returns:
            List[str]: List of validation warnings (empty if all valid)

        Raises:
            ValidationError: If requirements fail validation
        """
        pass

    def _validate_source(self) -> None:
        """Validate the source path exists and is accessible.

        Raises:
            FileAccessError: If source path doesn't exist or is inaccessible
        """
        if not self.source_path.exists():
            raise FileAccessError(
                message=f"Source path does not exist: {self.source_path}",
                file_path=str(self.source_path),
                operation="read"
            )
        if not self.source_path.is_file() and not self.source_path.is_dir():
            raise FileAccessError(
                message=f"Source path must be a file or directory: {self.source_path}",
                file_path=str(self.source_path),
                operation="read"
            )

    def _read_file(self, file_path: Path) -> str:
        """Read contents of a file.

        Args:
            file_path: Path to file to read

        Returns:
            str: Contents of the file

        Raises:
            FileAccessError: If file cannot be read
        """
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            raise FileAccessError(
                message=f"Failed to read file {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="read",
                details={"error": str(e)}
            )

    def _identify_resource_type(
        self,
        resource_name: str,
        resource_data: Dict[str, Any]
    ) -> ResourceType:
        """Identify the type of a resource from its definition.

        Args:
            resource_name: Name of the resource
            resource_data: Resource definition data

        Returns:
            ResourceType: The identified resource type

        Raises:
            ResourceTypeError: If resource type cannot be identified
        """
        # This is a basic implementation - subclasses should override with
        # source-specific logic for identifying resource types
        if 'type' in resource_data:
            try:
                return ResourceType(resource_data['type'])
            except ValueError:
                pass

        # Try to infer from resource name/properties
        name_lower = resource_name.lower()
        if any(x in name_lower for x in ['instance', 'vm', 'compute']):
            return ResourceType.COMPUTE
        if any(x in name_lower for x in ['storage', 'bucket', 'disk']):
            return ResourceType.STORAGE
        if any(x in name_lower for x in ['vpc', 'network', 'subnet']):
            return ResourceType.NETWORK
        if any(x in name_lower for x in ['db', 'database', 'sql']):
            return ResourceType.DATABASE
        if any(x in name_lower for x in ['container', 'pod', 'docker']):
            return ResourceType.CONTAINER
        if any(x in name_lower for x in ['function', 'lambda']):
            return ResourceType.SERVERLESS
        if any(x in name_lower for x in ['cache', 'redis', 'memcached']):
            return ResourceType.CACHE
        if any(x in name_lower for x in ['queue', 'topic', 'subscription']):
            return ResourceType.QUEUE
        if any(x in name_lower for x in ['lb', 'loadbalancer']):
            return ResourceType.LOAD_BALANCER
        if any(x in name_lower for x in ['dns', 'domain', 'zone']):
            return ResourceType.DNS
        if any(x in name_lower for x in ['cdn', 'cloudfront']):
            return ResourceType.CDN
        if any(x in name_lower for x in ['monitor', 'alert', 'log']):
            return ResourceType.MONITORING
        if any(x in name_lower for x in ['security', 'firewall', 'waf']):
            return ResourceType.SECURITY
        if any(x in name_lower for x in ['iam', 'role', 'policy']):
            return ResourceType.IAM

        raise ResourceTypeError(
            message=f"Could not identify resource type for {resource_name}",
            resource_name=resource_name,
            resource_type="unknown"
        )

    def _extract_dependencies(
        self,
        resource_data: Dict[str, Any]
    ) -> List[str]:
        """Extract resource dependencies from resource definition.

        Args:
            resource_data: Resource definition data

        Returns:
            List[str]: List of resource names this resource depends on
        """
        # This is a basic implementation - subclasses should override with
        # source-specific logic for extracting dependencies
        dependencies = set()

        def find_refs(data: Any) -> None:
            if isinstance(data, dict):
                for k, v in data.items():
                    if k.lower() in ['depends_on', 'dependson', 'dependencies']:
                        if isinstance(v, list):
                            dependencies.update(v)
                        elif isinstance(v, str):
                            dependencies.add(v)
                    else:
                        find_refs(v)
            elif isinstance(data, list):
                for item in data:
                    find_refs(item)

        find_refs(resource_data)
        return list(dependencies)

    def _extract_tags(
        self,
        resource_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract resource tags from resource definition.

        Args:
            resource_data: Resource definition data

        Returns:
            Dict[str, str]: Dictionary of tags
        """
        # This is a basic implementation - subclasses should override with
        # source-specific logic for extracting tags
        tags = {}
        if 'tags' in resource_data and isinstance(resource_data['tags'], dict):
            tags.update(resource_data['tags'])
        return tags


class ParserRegistry:
    """Registry of available infrastructure requirement parsers."""

    _parsers: Dict[SourceType, type[BaseParser]] = {}

    @classmethod
    def register(cls, source_type: SourceType, parser_class: type[BaseParser]) -> None:
        """Register a parser for a source type.

        Args:
            source_type: The source type the parser handles
            parser_class: The parser class to register
        """
        cls._parsers[source_type] = parser_class

    @classmethod
    def get_parser(
        cls,
        source_type: SourceType,
        source_path: Union[str, Path]
    ) -> BaseParser:
        """Get a parser instance for a source type.

        Args:
            source_type: The source type to get a parser for
            source_path: Path to pass to parser constructor

        Returns:
            BaseParser: Instance of appropriate parser for source type

        Raises:
            UnsupportedSourceError: If no parser is registered for source type
        """
        if source_type not in cls._parsers:
            raise UnsupportedSourceError(
                message=f"No parser registered for source type: {source_type}",
                source_type=source_type.value,
                supported_types=[t.value for t in cls._parsers.keys()]
            )
        return cls._parsers[source_type](source_path)

    @classmethod
    def get_supported_types(cls) -> Set[SourceType]:
        """Get set of supported source types.

        Returns:
            Set[SourceType]: Set of source types with registered parsers
        """
        return set(cls._parsers.keys())
