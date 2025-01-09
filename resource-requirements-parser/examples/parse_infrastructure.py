"""Example usage of the Resource Requirements Parser.

This script demonstrates how to use the Resource Requirements Parser to:
1. Parse Terraform and CloudFormation infrastructure definitions
2. Extract resource requirements
3. Analyze dependencies
4. Generate reports
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

from resource_requirements_parser import (
    ResourceType,
    SourceType,
    parse_requirements,
    get_supported_source_types,
)


def print_resource_summary(resource_type: ResourceType, resources: List[Dict]) -> None:
    """Print summary of resources by type.

    Args:
        resource_type: Type of resources to summarize
        resources: List of resources of that type
    """
    print(f"\n{resource_type.value.title()} Resources:")
    print("-" * 40)
    
    for resource in resources:
        print(f"- {resource['name']}")
        if resource_type == ResourceType.COMPUTE:
            print(f"  vCPUs: {resource['compute'].vcpus}")
            print(f"  Memory: {resource['compute'].memory_gb} GB")
            if resource['compute'].gpu_count:
                print(f"  GPUs: {resource['compute'].gpu_count}")
        elif resource_type == ResourceType.STORAGE:
            print(f"  Type: {resource['storage'].type.value}")
            print(f"  Capacity: {resource['storage'].capacity_gb} GB")
            print(f"  Encrypted: {resource['storage'].encryption_required}")
        elif resource_type == ResourceType.NETWORK:
            print(f"  Type: {resource['network'].type.value}")
            if resource['network'].cidr_block:
                print(f"  CIDR: {resource['network'].cidr_block}")
            print(f"  Public: {resource['network'].public_access}")
        elif resource_type == ResourceType.DATABASE:
            print(f"  Engine: {resource['database'].engine} {resource['database'].version}")
            print(f"  Storage: {resource['database'].storage_gb} GB")
            print(f"  Multi-AZ: {resource['database'].multi_az}")

        # Print tags if any
        if resource['tags']:
            print("  Tags:")
            for key, value in resource['tags'].items():
                print(f"    {key}: {value}")

        # Print dependencies if any
        if resource['dependencies']:
            print("  Dependencies:")
            for dep in resource['dependencies']:
                print(f"    - {dep}")
        print()


def analyze_infrastructure(source_path: str, source_type: SourceType) -> None:
    """Analyze infrastructure definition and print report.

    Args:
        source_path: Path to infrastructure definition file/directory
        source_type: Type of infrastructure definition (Terraform, CloudFormation, etc.)
    """
    print(f"\nAnalyzing {source_type.value} infrastructure in: {source_path}")
    print("=" * 80)

    # Parse infrastructure requirements
    result = parse_requirements(source_path, source_type)
    requirements = result.requirements

    # Print basic information
    print(f"\nInfrastructure Name: {requirements.name}")
    print(f"Source Type: {requirements.source_type.value}")
    print(f"Total Resources: {len(requirements.resources)}")

    # Print any warnings
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"- {warning}")

    # Group resources by type
    resources_by_type = {}
    for resource in requirements.resources:
        resources = resources_by_type.setdefault(resource.type, [])
        resources.append({
            'name': resource.name,
            'compute': resource.compute,
            'storage': resource.storage,
            'network': resource.network,
            'database': resource.database,
            'tags': resource.tags,
            'dependencies': resource.dependencies,
        })

    # Print resource summaries by type
    for resource_type in ResourceType:
        if resource_type in resources_by_type:
            print_resource_summary(resource_type, resources_by_type[resource_type])

    # Print global tags if any
    if requirements.global_tags:
        print("\nGlobal Tags:")
        for key, value in requirements.global_tags.items():
            print(f"- {key}: {value}")


def main():
    """Main entry point."""
    # Print supported source types
    print("Supported infrastructure definition types:")
    for source_type in get_supported_source_types():
        print(f"- {source_type.value}")

    # Example: Parse Terraform configuration
    terraform_path = "examples/terraform"
    if os.path.exists(terraform_path):
        analyze_infrastructure(terraform_path, SourceType.TERRAFORM)

    # Example: Parse CloudFormation template
    cloudformation_path = "examples/cloudformation/template.yaml"
    if os.path.exists(cloudformation_path):
        analyze_infrastructure(cloudformation_path, SourceType.CLOUDFORMATION)


if __name__ == "__main__":
    main()
