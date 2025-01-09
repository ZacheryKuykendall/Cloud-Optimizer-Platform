"""Tests for the Terraform plan parser."""

import json
from pathlib import Path
from typing import Dict, Any
import pytest

from terraform_cost_analyzer.exceptions import (
    ModuleParsingError,
    PlanParsingError,
    ResourceParsingError,
    ValidationError,
)
from terraform_cost_analyzer.models import (
    CloudProvider,
    ResourceAction,
    ResourceMetadata,
    ResourceType,
)
from terraform_cost_analyzer.parser import TerraformPlanParser


@pytest.fixture
def parser():
    """Create a TerraformPlanParser instance."""
    return TerraformPlanParser()


@pytest.fixture
def aws_ec2_plan():
    """Sample Terraform plan for AWS EC2 instance."""
    return {
        "resource_changes": [
            {
                "address": "aws_instance.example",
                "type": "aws_instance",
                "name": "example",
                "provider_name": "aws",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "instance_type": "t3.micro",
                        "region": "us-east-1",
                        "tags": {
                            "Environment": "production",
                            "Name": "example-instance"
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture
def azure_vm_plan():
    """Sample Terraform plan for Azure VM."""
    return {
        "resource_changes": [
            {
                "address": "azurerm_virtual_machine.example",
                "type": "azurerm_virtual_machine",
                "name": "example",
                "provider_name": "azurerm",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "size": "Standard_B2s",
                        "location": "eastus",
                        "tags": {
                            "Environment": "staging",
                            "Name": "example-vm"
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture
def gcp_instance_plan():
    """Sample Terraform plan for GCP Compute Instance."""
    return {
        "resource_changes": [
            {
                "address": "google_compute_instance.example",
                "type": "google_compute_instance",
                "name": "example",
                "provider_name": "google",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "machine_type": "n1-standard-1",
                        "zone": "us-central1-a",
                        "labels": {
                            "environment": "dev",
                            "name": "example-instance"
                        }
                    }
                }
            }
        ]
    }


def test_parse_aws_ec2(parser, aws_ec2_plan):
    """Test parsing AWS EC2 instance."""
    resources = parser.extract_resources(aws_ec2_plan)
    assert len(resources) == 1
    
    metadata, action = resources[0]
    assert isinstance(metadata, ResourceMetadata)
    assert action == ResourceAction.CREATE
    assert metadata.provider == CloudProvider.AWS
    assert metadata.type == "aws_instance"
    assert metadata.normalized_type == ResourceType.COMPUTE
    assert metadata.region == "us-east-1"
    assert metadata.specifications["instance_type"] == "t3.micro"
    assert "tags" in metadata.specifications


def test_parse_azure_vm(parser, azure_vm_plan):
    """Test parsing Azure VM."""
    resources = parser.extract_resources(azure_vm_plan)
    assert len(resources) == 1
    
    metadata, action = resources[0]
    assert isinstance(metadata, ResourceMetadata)
    assert action == ResourceAction.CREATE
    assert metadata.provider == CloudProvider.AZURE
    assert metadata.type == "azurerm_virtual_machine"
    assert metadata.normalized_type == ResourceType.COMPUTE
    assert metadata.region == "eastus"
    assert metadata.specifications["size"] == "Standard_B2s"
    assert "tags" in metadata.specifications


def test_parse_gcp_instance(parser, gcp_instance_plan):
    """Test parsing GCP Compute Instance."""
    resources = parser.extract_resources(gcp_instance_plan)
    assert len(resources) == 1
    
    metadata, action = resources[0]
    assert isinstance(metadata, ResourceMetadata)
    assert action == ResourceAction.CREATE
    assert metadata.provider == CloudProvider.GCP
    assert metadata.type == "google_compute_instance"
    assert metadata.normalized_type == ResourceType.COMPUTE
    assert "us-central1" in metadata.region
    assert metadata.specifications["machine_type"] == "n1-standard-1"
    assert "tags" in metadata.specifications


def test_parse_action(parser):
    """Test parsing different resource actions."""
    assert parser._parse_action({"actions": ["create"]}) == ResourceAction.CREATE
    assert parser._parse_action({"actions": ["update"]}) == ResourceAction.UPDATE
    assert parser._parse_action({"actions": ["delete"]}) == ResourceAction.DELETE
    assert parser._parse_action({"actions": []}) == ResourceAction.NO_CHANGE
    assert parser._parse_action({"actions": ["create", "delete"]}) == ResourceAction.UPDATE


def test_parse_provider(parser):
    """Test parsing different providers."""
    assert parser._parse_provider("aws") == CloudProvider.AWS
    assert parser._parse_provider("azurerm") == CloudProvider.AZURE
    assert parser._parse_provider("google") == CloudProvider.GCP
    assert parser._parse_provider("google-beta") == CloudProvider.GCP
    
    with pytest.raises(ValidationError):
        parser._parse_provider("unknown")


def test_extract_region(parser):
    """Test region extraction from different resource formats."""
    # Test provider config
    resource = {
        "provider_config": {"region": "us-west-2"}
    }
    assert parser._extract_region(resource) == "us-west-2"

    # Test resource attributes
    resource = {
        "change": {
            "after": {"region": "eu-west-1"}
        }
    }
    assert parser._extract_region(resource) == "eu-west-1"

    # Test Azure location
    resource = {
        "change": {
            "after": {"location": "eastus2"}
        }
    }
    assert parser._extract_region(resource) == "eastus2"

    # Test unknown region
    resource = {"change": {"after": {}}}
    assert parser._extract_region(resource) == "unknown"


def test_map_resource_type(parser):
    """Test resource type mapping."""
    assert parser._map_resource_type(CloudProvider.AWS, "aws_instance") == ResourceType.COMPUTE
    assert parser._map_resource_type(CloudProvider.AWS, "aws_s3_bucket") == ResourceType.STORAGE
    assert parser._map_resource_type(CloudProvider.AZURE, "azurerm_virtual_machine") == ResourceType.COMPUTE
    assert parser._map_resource_type(CloudProvider.GCP, "google_compute_instance") == ResourceType.COMPUTE
    assert parser._map_resource_type(CloudProvider.AWS, "unknown_type") == ResourceType.OTHER


def test_extract_modules(parser):
    """Test module extraction."""
    plan_data = {
        "resource_changes": [
            {"module_address": "module.vpc"},
            {"module_address": "module.ec2"},
            {"module_address": "module.vpc"}  # Duplicate
        ]
    }
    modules = parser.extract_modules(plan_data)
    assert modules == {"module.vpc", "module.ec2"}


def test_extract_providers(parser):
    """Test provider extraction."""
    plan_data = {
        "resource_changes": [
            {"provider_name": "aws"},
            {"provider_name": "azurerm"},
            {"provider_name": "google"},
            {"provider_name": "aws"},  # Duplicate
            {"provider_name": "unknown"}  # Invalid
        ]
    }
    providers = parser.extract_providers(plan_data)
    assert providers == {CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP}


def test_extract_regions(parser):
    """Test region extraction for each provider."""
    plan_data = {
        "resource_changes": [
            {
                "provider_name": "aws",
                "change": {"after": {"region": "us-east-1"}}
            },
            {
                "provider_name": "azurerm",
                "change": {"after": {"location": "eastus"}}
            },
            {
                "provider_name": "google",
                "change": {"after": {"zone": "us-central1-a"}}
            }
        ]
    }
    regions = parser.extract_regions(plan_data)
    assert "us-east-1" in regions[CloudProvider.AWS]
    assert "eastus" in regions[CloudProvider.AZURE]
    assert "us-central1" in regions[CloudProvider.GCP]


def test_error_handling(parser):
    """Test error handling scenarios."""
    # Test invalid plan file
    with pytest.raises(PlanParsingError):
        parser.parse_plan_file("nonexistent.json")

    # Test invalid resource
    plan_data = {
        "resource_changes": [
            {
                "type": "invalid_type",
                "name": "example",
                "provider_name": "unknown"
            }
        ]
    }
    with pytest.raises(ResourceParsingError):
        parser.extract_resources(plan_data)

    # Test invalid module
    plan_data = {
        "resource_changes": [
            {"module_address": None}
        ]
    }
    with pytest.raises(ModuleParsingError):
        parser.extract_modules(plan_data)


def test_specifications_extraction(parser):
    """Test extraction of resource specifications."""
    resource = {
        "change": {
            "after": {
                "instance_type": "t3.large",
                "size": "Standard_DS2_v2",
                "tier": "Standard",
                "sku": "P1v2",
                "tags": {
                    "Environment": "production",
                    "Team": "platform"
                }
            }
        }
    }
    specs = parser._extract_specifications(resource)
    assert specs["instance_type"] == "t3.large"
    assert specs["size"] == "Standard_DS2_v2"
    assert specs["tier"] == "Standard"
    assert specs["sku"] == "P1v2"
    assert "tags" in specs
    assert json.loads(specs["tags"])["Environment"] == "production"
