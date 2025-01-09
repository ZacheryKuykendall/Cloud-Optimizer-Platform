"""Terraform Parser Implementation.

This module provides a parser for extracting resource requirements from
Terraform configuration files (.tf, .tfvars).
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import hcl2

from resource_requirements_parser.models import (
    InfrastructureRequirements,
    ParsingResult,
    ResourceRequirements,
    ResourceType,
    SourceType,
    ComputeRequirements,
    StorageRequirements,
    NetworkRequirements,
    DatabaseRequirements,
    ComputeType,
    StorageType,
    NetworkType,
    DatabaseType,
)
from resource_requirements_parser.exceptions import (
    ParsingError,
    ValidationError,
    ResourceTypeError,
    FileAccessError,
    VariableResolutionError,
    ModuleResolutionError,
)
from resource_requirements_parser.parser import BaseParser


class TerraformParser(BaseParser):
    """Parser for Terraform configuration files."""

    # Common Terraform resource type prefixes
    COMPUTE_PREFIXES = {
        'aws_instance', 'aws_launch_template', 'aws_autoscaling_group',
        'azurerm_virtual_machine', 'azurerm_linux_virtual_machine',
        'azurerm_windows_virtual_machine', 'google_compute_instance',
        'google_container_cluster',
    }

    STORAGE_PREFIXES = {
        'aws_s3_bucket', 'aws_ebs_volume', 'aws_efs_file_system',
        'azurerm_storage_account', 'azurerm_managed_disk',
        'google_storage_bucket', 'google_compute_disk',
    }

    NETWORK_PREFIXES = {
        'aws_vpc', 'aws_subnet', 'aws_security_group', 'aws_route_table',
        'azurerm_virtual_network', 'azurerm_subnet', 'azurerm_network_security_group',
        'google_compute_network', 'google_compute_subnetwork',
        'google_compute_firewall',
    }

    DATABASE_PREFIXES = {
        'aws_db_instance', 'aws_rds_cluster', 'aws_dynamodb_table',
        'azurerm_sql_server', 'azurerm_mysql_server', 'azurerm_postgresql_server',
        'google_sql_database_instance', 'google_spanner_instance',
    }

    def __init__(self, source_path: Union[str, Path]):
        """Initialize Terraform parser.

        Args:
            source_path: Path to Terraform configuration file or directory
        """
        super().__init__(source_path)
        self.variables: Dict[str, Any] = {}
        self.modules: Dict[str, Dict[str, Any]] = {}

    def get_source_type(self) -> SourceType:
        """Get the source type for Terraform configurations.

        Returns:
            SourceType: TERRAFORM
        """
        return SourceType.TERRAFORM

    def parse(self) -> ParsingResult:
        """Parse Terraform configuration files.

        Returns:
            ParsingResult: Parsed infrastructure requirements

        Raises:
            ParsingError: If there are errors parsing Terraform files
            ValidationError: If parsed requirements fail validation
            FileAccessError: If there are issues accessing Terraform files
        """
        try:
            # Parse variables first
            self._parse_variables()

            # Parse all .tf files
            config = self._parse_terraform_files()

            # Extract resources
            resources = []
            warnings = []
            for resource_type, instances in config.get('resource', {}).items():
                for name, data in instances.items():
                    try:
                        resource = self._parse_resource(resource_type, name, data)
                        if resource:
                            resources.append(resource)
                    except (ResourceTypeError, ValidationError) as e:
                        warnings.append(str(e))

            # Create infrastructure requirements
            requirements = InfrastructureRequirements(
                name=Path(self.source_path).stem,
                source_type=SourceType.TERRAFORM,
                source_path=str(self.source_path),
                resources=resources,
                global_tags=self._extract_global_tags(config),
                metadata={
                    'terraform_version': self._get_terraform_version(config),
                    'provider_versions': self._get_provider_versions(config),
                }
            )

            # Validate
            validation_warnings = self.validate(requirements)
            warnings.extend(validation_warnings)

            return ParsingResult(
                requirements=requirements,
                warnings=warnings,
                metadata={
                    'parsed_files': self._get_parsed_files(),
                    'variable_files': self._get_variable_files(),
                }
            )

        except Exception as e:
            raise ParsingError(
                message=f"Failed to parse Terraform configuration: {str(e)}",
                source_type=SourceType.TERRAFORM.value,
                source_path=str(self.source_path),
                details={"error": str(e)}
            )

    def validate(self, requirements: InfrastructureRequirements) -> List[str]:
        """Validate parsed Terraform requirements.

        Args:
            requirements: The requirements to validate

        Returns:
            List[str]: List of validation warnings

        Raises:
            ValidationError: If requirements fail validation
        """
        warnings = []

        # Check for missing required provider blocks
        if not self._has_required_providers():
            warnings.append("No required_providers block found")

        # Check for resources without proper dependencies
        for resource in requirements.resources:
            if not resource.dependencies and not self._is_root_resource(resource):
                warnings.append(
                    f"Resource {resource.name} has no dependencies defined"
                )

        # Validate compute requirements
        compute_resources = requirements.get_resources_by_type(ResourceType.COMPUTE)
        for resource in compute_resources:
            if not resource.compute:
                warnings.append(
                    f"Compute resource {resource.name} missing compute requirements"
                )
            elif not resource.compute.instance_count:
                warnings.append(
                    f"Compute resource {resource.name} missing instance count"
                )

        return warnings

    def _parse_variables(self) -> None:
        """Parse Terraform variable files (.tfvars).

        Raises:
            VariableResolutionError: If variables cannot be parsed
        """
        try:
            # Parse .tfvars files
            for var_file in self.source_path.glob('*.tfvars'):
                with open(var_file) as f:
                    vars_data = hcl2.load(f)
                    self.variables.update(vars_data)

            # Parse variables from environment
            for key, value in os.environ.items():
                if key.startswith('TF_VAR_'):
                    var_name = key[7:]  # Remove TF_VAR_ prefix
                    self.variables[var_name] = value

        except Exception as e:
            raise VariableResolutionError(
                message=f"Failed to parse Terraform variables: {str(e)}",
                variable_name="multiple",
                source_type=SourceType.TERRAFORM.value,
                details={"error": str(e)}
            )

    def _parse_terraform_files(self) -> Dict[str, Any]:
        """Parse all Terraform configuration files in source path.

        Returns:
            Dict[str, Any]: Combined Terraform configuration

        Raises:
            ParsingError: If Terraform files cannot be parsed
        """
        config: Dict[str, Any] = {}

        try:
            # Parse all .tf files
            for tf_file in self.source_path.glob('*.tf'):
                with open(tf_file) as f:
                    file_config = hcl2.load(f)
                    self._merge_config(config, file_config)

            return config

        except Exception as e:
            raise ParsingError(
                message=f"Failed to parse Terraform files: {str(e)}",
                source_type=SourceType.TERRAFORM.value,
                source_path=str(self.source_path),
                details={"error": str(e)}
            )

    def _merge_config(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> None:
        """Merge Terraform configurations.

        Args:
            base: Base configuration to merge into
            overlay: Configuration to merge
        """
        for key, value in overlay.items():
            if key not in base:
                base[key] = value
            elif isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            elif isinstance(base[key], list) and isinstance(value, list):
                base[key].extend(value)
            else:
                base[key] = value

    def _parse_resource(
        self,
        resource_type: str,
        name: str,
        data: Dict[str, Any]
    ) -> Optional[ResourceRequirements]:
        """Parse a Terraform resource into requirements.

        Args:
            resource_type: Terraform resource type (e.g., aws_instance)
            name: Resource name
            data: Resource configuration data

        Returns:
            Optional[ResourceRequirements]: Parsed requirements or None if resource
            should be skipped

        Raises:
            ResourceTypeError: If resource type cannot be determined
            ValidationError: If resource data is invalid
        """
        try:
            # Determine resource type
            resource_category = self._get_resource_category(resource_type)
            if not resource_category:
                return None  # Skip resources we don't handle

            # Extract common fields
            requirements = ResourceRequirements(
                name=f"{resource_type}.{name}",
                type=resource_category,
                tags=self._extract_tags(data),
                dependencies=self._extract_dependencies(data)
            )

            # Parse specific requirements based on type
            if resource_category == ResourceType.COMPUTE:
                requirements.compute = self._parse_compute_requirements(
                    resource_type, data
                )
            elif resource_category == ResourceType.STORAGE:
                requirements.storage = self._parse_storage_requirements(
                    resource_type, data
                )
            elif resource_category == ResourceType.NETWORK:
                requirements.network = self._parse_network_requirements(
                    resource_type, data
                )
            elif resource_category == ResourceType.DATABASE:
                requirements.database = self._parse_database_requirements(
                    resource_type, data
                )

            return requirements

        except Exception as e:
            raise ValidationError(
                message=f"Failed to parse resource {resource_type}.{name}: {str(e)}",
                resource_name=name,
                details={"error": str(e)}
            )

    def _get_resource_category(self, resource_type: str) -> Optional[ResourceType]:
        """Get the resource category for a Terraform resource type.

        Args:
            resource_type: Terraform resource type (e.g., aws_instance)

        Returns:
            Optional[ResourceType]: Resource category or None if not handled
        """
        if any(resource_type.startswith(prefix) for prefix in self.COMPUTE_PREFIXES):
            return ResourceType.COMPUTE
        if any(resource_type.startswith(prefix) for prefix in self.STORAGE_PREFIXES):
            return ResourceType.STORAGE
        if any(resource_type.startswith(prefix) for prefix in self.NETWORK_PREFIXES):
            return ResourceType.NETWORK
        if any(resource_type.startswith(prefix) for prefix in self.DATABASE_PREFIXES):
            return ResourceType.DATABASE
        return None

    def _parse_compute_requirements(
        self,
        resource_type: str,
        data: Dict[str, Any]
    ) -> ComputeRequirements:
        """Parse compute requirements from resource data.

        Args:
            resource_type: Terraform resource type
            data: Resource configuration data

        Returns:
            ComputeRequirements: Parsed compute requirements
        """
        # Extract instance type/size
        instance_type = data.get('instance_type', data.get('size', 'unknown'))

        # Parse CPU and memory from instance type
        vcpus, memory_gb = self._parse_instance_specs(instance_type)

        return ComputeRequirements(
            type=ComputeType.VM,  # Could be more specific based on resource_type
            vcpus=vcpus,
            memory_gb=memory_gb,
            instance_count=self._get_instance_count(data),
            operating_system=self._get_operating_system(data),
            availability_zones=self._get_availability_zones(data),
            custom_requirements={
                'instance_type': instance_type,
                'resource_type': resource_type,
            }
        )

    def _parse_storage_requirements(
        self,
        resource_type: str,
        data: Dict[str, Any]
    ) -> StorageRequirements:
        """Parse storage requirements from resource data.

        Args:
            resource_type: Terraform resource type
            data: Resource configuration data

        Returns:
            StorageRequirements: Parsed storage requirements
        """
        return StorageRequirements(
            type=self._get_storage_type(resource_type),
            capacity_gb=self._get_storage_size(data),
            iops=data.get('iops'),
            throughput_mbps=data.get('throughput'),
            encryption_required='encryption' in data or data.get('encrypted', False),
            backup_required='backup' in data or data.get('backup_retention_period', 0) > 0,
            replication_required='replication' in data or data.get('replica', False),
            custom_requirements={
                'resource_type': resource_type,
            }
        )

    def _parse_network_requirements(
        self,
        resource_type: str,
        data: Dict[str, Any]
    ) -> NetworkRequirements:
        """Parse network requirements from resource data.

        Args:
            resource_type: Terraform resource type
            data: Resource configuration data

        Returns:
            NetworkRequirements: Parsed network requirements
        """
        return NetworkRequirements(
            type=self._get_network_type(resource_type),
            cidr_block=data.get('cidr_block'),
            port_ranges=self._parse_port_ranges(data),
            protocols=self._parse_protocols(data),
            public_access=self._has_public_access(data),
            vpn_required='vpn' in resource_type.lower(),
            custom_requirements={
                'resource_type': resource_type,
            }
        )

    def _parse_database_requirements(
        self,
        resource_type: str,
        data: Dict[str, Any]
    ) -> DatabaseRequirements:
        """Parse database requirements from resource data.

        Args:
            resource_type: Terraform resource type
            data: Resource configuration data

        Returns:
            DatabaseRequirements: Parsed database requirements
        """
        return DatabaseRequirements(
            type=self._get_database_type(resource_type),
            engine=data.get('engine', 'unknown'),
            version=str(data.get('engine_version', 'latest')),
            storage_gb=self._get_database_storage(data),
            multi_az=data.get('multi_az', False),
            backup_retention_days=data.get('backup_retention_period'),
            encryption_required=data.get('storage_encrypted', True),
            custom_requirements={
                'resource_type': resource_type,
            }
        )

    def _get_terraform_version(self, config: Dict[str, Any]) -> Optional[str]:
        """Get Terraform version from configuration.

        Args:
            config: Terraform configuration

        Returns:
            Optional[str]: Terraform version constraint if specified
        """
        if 'terraform' in config:
            return config['terraform'].get('required_version')
        return None

    def _get_provider_versions(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get provider version constraints from configuration.

        Args:
            config: Terraform configuration

        Returns:
            Dict[str, str]: Provider version constraints
        """
        versions = {}
        if 'terraform' in config:
            required = config['terraform'].get('required_providers', {})
            for provider, data in required.items():
                if isinstance(data, dict):
                    versions[provider] = data.get('version', 'latest')
                else:
                    versions[provider] = str(data)
        return versions

    def _get_parsed_files(self) -> List[str]:
        """Get list of parsed Terraform files.

        Returns:
            List[str]: List of parsed file paths
        """
        return [
            str(f.relative_to(self.source_path))
            for f in self.source_path.glob('*.tf')
        ]

    def _get_variable_files(self) -> List[str]:
        """Get list of parsed variable files.

        Returns:
            List[str]: List of parsed variable file paths
        """
        return [
            str(f.relative_to(self.source_path))
            for f in self.source_path.glob('*.tfvars')
        ]

    def _has_required_providers(self) -> bool:
        """Check if configuration has required_providers block.

        Returns:
            bool: True if required_providers is defined
        """
        try:
            with open(self.source_path / 'versions.tf') as f:
                config = hcl2.load(f)
                return 'required_providers' in config.get('terraform', {})
        except:
            return False

    def _is_root_resource(self, resource: ResourceRequirements) -> bool:
        """Check if a resource is a root-level resource.

        Args:
            resource: Resource to check

        Returns:
            bool: True if resource is root-level
        """
        # Root resources typically include VPC, security groups, etc.
        return resource.type in {
            ResourceType.NETWORK,
            ResourceType.SECURITY,
            ResourceType.IAM
        }
