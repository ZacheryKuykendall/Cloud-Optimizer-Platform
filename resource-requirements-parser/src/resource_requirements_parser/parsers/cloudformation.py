"""CloudFormation Parser Implementation.

This module provides a parser for extracting resource requirements from
AWS CloudFormation templates (.yaml, .json).
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

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
    TemplateFormatError,
    VariableResolutionError,
)
from resource_requirements_parser.parser import BaseParser


class CloudFormationParser(BaseParser):
    """Parser for AWS CloudFormation templates."""

    # Common CloudFormation resource types
    COMPUTE_TYPES = {
        'AWS::EC2::Instance',
        'AWS::AutoScaling::LaunchConfiguration',
        'AWS::AutoScaling::LaunchTemplate',
        'AWS::ECS::TaskDefinition',
        'AWS::Lambda::Function',
    }

    STORAGE_TYPES = {
        'AWS::S3::Bucket',
        'AWS::EBS::Volume',
        'AWS::EFS::FileSystem',
        'AWS::FSx::FileSystem',
    }

    NETWORK_TYPES = {
        'AWS::EC2::VPC',
        'AWS::EC2::Subnet',
        'AWS::EC2::SecurityGroup',
        'AWS::EC2::RouteTable',
        'AWS::EC2::VPNGateway',
    }

    DATABASE_TYPES = {
        'AWS::RDS::DBInstance',
        'AWS::RDS::DBCluster',
        'AWS::DynamoDB::Table',
        'AWS::ElastiCache::CacheCluster',
    }

    def __init__(self, source_path: Union[str, Path]):
        """Initialize CloudFormation parser.

        Args:
            source_path: Path to CloudFormation template file
        """
        super().__init__(source_path)
        self.parameters: Dict[str, Any] = {}
        self.conditions: Dict[str, Any] = {}

    def get_source_type(self) -> SourceType:
        """Get the source type for CloudFormation templates.

        Returns:
            SourceType: CLOUDFORMATION
        """
        return SourceType.CLOUDFORMATION

    def parse(self) -> ParsingResult:
        """Parse CloudFormation template.

        Returns:
            ParsingResult: Parsed infrastructure requirements

        Raises:
            ParsingError: If there are errors parsing the template
            ValidationError: If parsed requirements fail validation
            FileAccessError: If there are issues accessing template file
        """
        try:
            # Load and parse template
            template = self._load_template()

            # Validate template format
            self._validate_template_format(template)

            # Parse parameters and conditions
            self._parse_parameters(template.get('Parameters', {}))
            self._parse_conditions(template.get('Conditions', {}))

            # Extract resources
            resources = []
            warnings = []
            for resource_id, resource_data in template.get('Resources', {}).items():
                try:
                    resource = self._parse_resource(resource_id, resource_data)
                    if resource:
                        resources.append(resource)
                except (ResourceTypeError, ValidationError) as e:
                    warnings.append(str(e))

            # Create infrastructure requirements
            requirements = InfrastructureRequirements(
                name=Path(self.source_path).stem,
                source_type=SourceType.CLOUDFORMATION,
                source_path=str(self.source_path),
                resources=resources,
                global_tags=self._extract_global_tags(template),
                metadata={
                    'template_format_version': template.get('AWSTemplateFormatVersion'),
                    'description': template.get('Description'),
                    'transform': template.get('Transform'),
                }
            )

            # Validate
            validation_warnings = self.validate(requirements)
            warnings.extend(validation_warnings)

            return ParsingResult(
                requirements=requirements,
                warnings=warnings,
                metadata={
                    'parameter_count': len(self.parameters),
                    'condition_count': len(self.conditions),
                }
            )

        except Exception as e:
            raise ParsingError(
                message=f"Failed to parse CloudFormation template: {str(e)}",
                source_type=SourceType.CLOUDFORMATION.value,
                source_path=str(self.source_path),
                details={"error": str(e)}
            )

    def validate(self, requirements: InfrastructureRequirements) -> List[str]:
        """Validate parsed CloudFormation requirements.

        Args:
            requirements: The requirements to validate

        Returns:
            List[str]: List of validation warnings

        Raises:
            ValidationError: If requirements fail validation
        """
        warnings = []

        # Check for resources without proper dependencies
        for resource in requirements.resources:
            if not resource.dependencies and not self._is_root_resource(resource):
                warnings.append(
                    f"Resource {resource.name} has no DependsOn defined"
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

    def _load_template(self) -> Dict[str, Any]:
        """Load and parse CloudFormation template file.

        Returns:
            Dict[str, Any]: Parsed template data

        Raises:
            FileAccessError: If template file cannot be read
            TemplateFormatError: If template format is invalid
        """
        try:
            content = self._read_file(self.source_path)
            if self.source_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(content)
            elif self.source_path.suffix == '.json':
                return json.loads(content)
            else:
                raise TemplateFormatError(
                    message="Unsupported template format",
                    source_type=SourceType.CLOUDFORMATION.value,
                    details={"file_extension": self.source_path.suffix}
                )
        except yaml.YAMLError as e:
            raise TemplateFormatError(
                message=f"Invalid YAML format: {str(e)}",
                source_type=SourceType.CLOUDFORMATION.value,
                details={"error": str(e)}
            )
        except json.JSONDecodeError as e:
            raise TemplateFormatError(
                message=f"Invalid JSON format: {str(e)}",
                source_type=SourceType.CLOUDFORMATION.value,
                details={"error": str(e)}
            )

    def _validate_template_format(self, template: Dict[str, Any]) -> None:
        """Validate CloudFormation template format.

        Args:
            template: Template data to validate

        Raises:
            TemplateFormatError: If template format is invalid
        """
        if 'Resources' not in template:
            raise TemplateFormatError(
                message="Template missing Resources section",
                source_type=SourceType.CLOUDFORMATION.value
            )

        version = template.get('AWSTemplateFormatVersion')
        if version and version not in ['2010-09-09']:
            raise TemplateFormatError(
                message=f"Unsupported template version: {version}",
                source_type=SourceType.CLOUDFORMATION.value,
                template_version=version
            )

    def _parse_parameters(self, parameters: Dict[str, Any]) -> None:
        """Parse template parameters.

        Args:
            parameters: Parameters section of template

        Raises:
            VariableResolutionError: If parameters cannot be parsed
        """
        try:
            for param_name, param_data in parameters.items():
                # Store parameter with its default value if any
                self.parameters[param_name] = param_data.get('Default')
        except Exception as e:
            raise VariableResolutionError(
                message=f"Failed to parse parameters: {str(e)}",
                variable_name="multiple",
                source_type=SourceType.CLOUDFORMATION.value,
                details={"error": str(e)}
            )

    def _parse_conditions(self, conditions: Dict[str, Any]) -> None:
        """Parse template conditions.

        Args:
            conditions: Conditions section of template
        """
        self.conditions = conditions

    def _parse_resource(
        self,
        resource_id: str,
        resource_data: Dict[str, Any]
    ) -> Optional[ResourceRequirements]:
        """Parse a CloudFormation resource into requirements.

        Args:
            resource_id: Resource logical ID
            resource_data: Resource definition data

        Returns:
            Optional[ResourceRequirements]: Parsed requirements or None if resource
            should be skipped

        Raises:
            ResourceTypeError: If resource type cannot be determined
            ValidationError: If resource data is invalid
        """
        try:
            resource_type = resource_data.get('Type')
            if not resource_type:
                raise ResourceTypeError(
                    message=f"Resource missing Type: {resource_id}",
                    resource_name=resource_id,
                    resource_type="unknown"
                )

            # Get resource category
            resource_category = self._get_resource_category(resource_type)
            if not resource_category:
                return None  # Skip resources we don't handle

            # Extract properties
            properties = resource_data.get('Properties', {})

            # Create base requirements
            requirements = ResourceRequirements(
                name=resource_id,
                type=resource_category,
                tags=self._extract_tags(properties),
                dependencies=self._extract_dependencies(resource_data)
            )

            # Parse specific requirements based on type
            if resource_category == ResourceType.COMPUTE:
                requirements.compute = self._parse_compute_requirements(
                    resource_type, properties
                )
            elif resource_category == ResourceType.STORAGE:
                requirements.storage = self._parse_storage_requirements(
                    resource_type, properties
                )
            elif resource_category == ResourceType.NETWORK:
                requirements.network = self._parse_network_requirements(
                    resource_type, properties
                )
            elif resource_category == ResourceType.DATABASE:
                requirements.database = self._parse_database_requirements(
                    resource_type, properties
                )

            return requirements

        except Exception as e:
            raise ValidationError(
                message=f"Failed to parse resource {resource_id}: {str(e)}",
                resource_name=resource_id,
                details={"error": str(e)}
            )

    def _get_resource_category(self, resource_type: str) -> Optional[ResourceType]:
        """Get the resource category for a CloudFormation resource type.

        Args:
            resource_type: CloudFormation resource type

        Returns:
            Optional[ResourceType]: Resource category or None if not handled
        """
        if resource_type in self.COMPUTE_TYPES:
            return ResourceType.COMPUTE
        if resource_type in self.STORAGE_TYPES:
            return ResourceType.STORAGE
        if resource_type in self.NETWORK_TYPES:
            return ResourceType.NETWORK
        if resource_type in self.DATABASE_TYPES:
            return ResourceType.DATABASE
        return None

    def _parse_compute_requirements(
        self,
        resource_type: str,
        properties: Dict[str, Any]
    ) -> ComputeRequirements:
        """Parse compute requirements from resource properties.

        Args:
            resource_type: CloudFormation resource type
            properties: Resource properties

        Returns:
            ComputeRequirements: Parsed compute requirements
        """
        instance_type = properties.get('InstanceType', 'unknown')
        vcpus, memory_gb = self._parse_instance_specs(instance_type)

        return ComputeRequirements(
            type=self._get_compute_type(resource_type),
            vcpus=vcpus,
            memory_gb=memory_gb,
            instance_count=self._get_instance_count(properties),
            operating_system=self._get_operating_system(properties),
            availability_zones=properties.get('AvailabilityZones', []),
            custom_requirements={
                'instance_type': instance_type,
                'resource_type': resource_type,
            }
        )

    def _parse_storage_requirements(
        self,
        resource_type: str,
        properties: Dict[str, Any]
    ) -> StorageRequirements:
        """Parse storage requirements from resource properties.

        Args:
            resource_type: CloudFormation resource type
            properties: Resource properties

        Returns:
            StorageRequirements: Parsed storage requirements
        """
        return StorageRequirements(
            type=self._get_storage_type(resource_type),
            capacity_gb=self._get_storage_size(properties),
            iops=properties.get('Iops'),
            throughput_mbps=properties.get('Throughput'),
            encryption_required=properties.get('Encrypted', False),
            backup_required='Backup' in properties,
            replication_required='Replication' in properties,
            custom_requirements={
                'resource_type': resource_type,
            }
        )

    def _parse_network_requirements(
        self,
        resource_type: str,
        properties: Dict[str, Any]
    ) -> NetworkRequirements:
        """Parse network requirements from resource properties.

        Args:
            resource_type: CloudFormation resource type
            properties: Resource properties

        Returns:
            NetworkRequirements: Parsed network requirements
        """
        return NetworkRequirements(
            type=self._get_network_type(resource_type),
            cidr_block=properties.get('CidrBlock'),
            port_ranges=self._parse_security_group_rules(properties),
            protocols=self._parse_protocols(properties),
            public_access=self._has_public_access(properties),
            vpn_required='VPN' in resource_type,
            custom_requirements={
                'resource_type': resource_type,
            }
        )

    def _parse_database_requirements(
        self,
        resource_type: str,
        properties: Dict[str, Any]
    ) -> DatabaseRequirements:
        """Parse database requirements from resource properties.

        Args:
            resource_type: CloudFormation resource type
            properties: Resource properties

        Returns:
            DatabaseRequirements: Parsed database requirements
        """
        return DatabaseRequirements(
            type=self._get_database_type(resource_type),
            engine=properties.get('Engine', 'unknown'),
            version=str(properties.get('EngineVersion', 'latest')),
            storage_gb=self._get_database_storage(properties),
            multi_az=properties.get('MultiAZ', False),
            backup_retention_days=properties.get('BackupRetentionPeriod'),
            encryption_required=properties.get('StorageEncrypted', True),
            custom_requirements={
                'resource_type': resource_type,
            }
        )

    def _extract_dependencies(self, resource_data: Dict[str, Any]) -> List[str]:
        """Extract resource dependencies.

        Args:
            resource_data: Resource definition data

        Returns:
            List[str]: List of resource dependencies
        """
        dependencies = set()

        # Check DependsOn
        depends_on = resource_data.get('DependsOn', [])
        if isinstance(depends_on, str):
            dependencies.add(depends_on)
        elif isinstance(depends_on, list):
            dependencies.update(depends_on)

        # Check Ref and Fn::GetAtt in Properties
        self._find_refs(resource_data.get('Properties', {}), dependencies)

        return list(dependencies)

    def _find_refs(self, data: Any, refs: Set[str]) -> None:
        """Recursively find Ref and GetAtt functions in template.

        Args:
            data: Data to search
            refs: Set to collect references in
        """
        if isinstance(data, dict):
            if 'Ref' in data and isinstance(data['Ref'], str):
                refs.add(data['Ref'])
            elif 'Fn::GetAtt' in data and isinstance(data['Fn::GetAtt'], list):
                refs.add(data['Fn::GetAtt'][0])
            for value in data.values():
                self._find_refs(value, refs)
        elif isinstance(data, list):
            for item in data:
                self._find_refs(item, refs)

    def _parse_security_group_rules(
        self,
        properties: Dict[str, Any]
    ) -> List[Dict[str, int]]:
        """Parse security group ingress/egress rules.

        Args:
            properties: Resource properties

        Returns:
            List[Dict[str, int]]: List of port ranges
        """
        port_ranges = []
        for rule_type in ['SecurityGroupIngress', 'SecurityGroupEgress']:
            for rule in properties.get(rule_type, []):
                if 'FromPort' in rule and 'ToPort' in rule:
                    port_ranges.append({
                        'from_port': rule['FromPort'],
                        'to_port': rule['ToPort']
                    })
        return port_ranges

    def _get_compute_type(self, resource_type: str) -> ComputeType:
        """Get compute type from resource type.

        Args:
            resource_type: CloudFormation resource type

        Returns:
            ComputeType: Type of compute resource
        """
        if 'Lambda' in resource_type:
            return ComputeType.FUNCTION
        if 'ECS' in resource_type:
            return ComputeType.CONTAINER
        return ComputeType.VM

    def _get_storage_type(self, resource_type: str) -> StorageType:
        """Get storage type from resource type.

        Args:
            resource_type: CloudFormation resource type

        Returns:
            StorageType: Type of storage resource
        """
        if 'S3' in resource_type:
            return StorageType.OBJECT
        if 'EFS' in resource_type:
            return StorageType.FILE
        return StorageType.BLOCK

    def _get_network_type(self, resource_type: str) -> NetworkType:
        """Get network type from resource type.

        Args:
            resource_type: CloudFormation resource type

        Returns:
            NetworkType: Type of network resource
        """
        if 'VPC' in resource_type:
            return NetworkType.VPC
        if 'Subnet' in resource_type:
            return NetworkType.SUBNET
        if 'RouteTable' in resource_type:
            return NetworkType.ROUTE_TABLE
        if 'SecurityGroup' in resource_type:
            return NetworkType.SECURITY_GROUP
        if 'VPNGateway' in resource_type:
            return NetworkType.VPN
        return NetworkType.FIREWALL

    def _get_database_type(self, resource_type: str) -> DatabaseType:
        """Get database type from resource type.

        Args:
            resource_type: CloudFormation resource type

        Returns:
            DatabaseType: Type of database resource
        """
        if 'DynamoDB' in resource_type:
            return DatabaseType.NOSQL
        if 'ElastiCache' in resource_type:
            return DatabaseType.CACHE
        return DatabaseType.RELATIONAL
