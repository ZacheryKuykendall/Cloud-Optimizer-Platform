"""Tests for the CloudFormation parser implementation."""

import os
from pathlib import Path
import pytest
import yaml
from textwrap import dedent

from resource_requirements_parser import (
    ResourceType,
    ComputeType,
    StorageType,
    NetworkType,
    DatabaseType,
    SourceType,
    parse_requirements,
)
from resource_requirements_parser.exceptions import (
    ParsingError,
    ValidationError,
    ResourceTypeError,
    TemplateFormatError,
)
from resource_requirements_parser.parsers.cloudformation import CloudFormationParser


@pytest.fixture
def temp_cloudformation_dir(tmp_path):
    """Create a temporary directory with CloudFormation template."""
    # Create template with various resource types
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Test CloudFormation template",
        "Parameters": {
            "EnvironmentName": {
                "Type": "String",
                "Default": "production",
                "Description": "Environment name"
            }
        },
        "Resources": {
            "WebServer": {
                "Type": "AWS::EC2::Instance",
                "Properties": {
                    "ImageId": "ami-0c55b159cbfafe1f0",
                    "InstanceType": "t2.micro",
                    "Tags": [
                        {"Key": "Name", "Value": "web-server"},
                        {"Key": "Environment", "Value": {"Ref": "EnvironmentName"}}
                    ]
                }
            },
            "DataBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": "my-data-bucket",
                    "Tags": [
                        {"Key": "Environment", "Value": {"Ref": "EnvironmentName"}}
                    ]
                }
            },
            "MainVPC": {
                "Type": "AWS::EC2::VPC",
                "Properties": {
                    "CidrBlock": "10.0.0.0/16",
                    "Tags": [
                        {"Key": "Name", "Value": "main"}
                    ]
                }
            },
            "Database": {
                "Type": "AWS::RDS::DBInstance",
                "Properties": {
                    "Engine": "mysql",
                    "EngineVersion": "5.7",
                    "DBInstanceClass": "db.t2.micro",
                    "AllocatedStorage": 20,
                    "StorageEncrypted": True,
                    "MultiAZ": False,
                    "Tags": [
                        {"Key": "Environment", "Value": {"Ref": "EnvironmentName"}}
                    ]
                }
            }
        }
    }

    # Write template file
    cf_dir = tmp_path / "cloudformation"
    cf_dir.mkdir()
    template_path = cf_dir / "template.yaml"
    template_path.write_text(yaml.dump(template))

    return cf_dir


def test_cloudformation_parser_initialization():
    """Test that the parser can be initialized with a path."""
    parser = CloudFormationParser("dummy/path")
    assert parser.get_source_type() == SourceType.CLOUDFORMATION


def test_parse_cloudformation_template(temp_cloudformation_dir):
    """Test parsing a complete CloudFormation template."""
    result = parse_requirements(
        str(temp_cloudformation_dir / "template.yaml"),
        SourceType.CLOUDFORMATION
    )
    
    # Verify basic parsing succeeded
    assert result.requirements is not None
    assert len(result.requirements.resources) == 4
    assert not result.errors

    # Get resources by type
    compute = result.requirements.get_resources_by_type(ResourceType.COMPUTE)
    storage = result.requirements.get_resources_by_type(ResourceType.STORAGE)
    network = result.requirements.get_resources_by_type(ResourceType.NETWORK)
    database = result.requirements.get_resources_by_type(ResourceType.DATABASE)

    # Verify compute resource
    assert len(compute) == 1
    web_server = compute[0]
    assert web_server.name == "WebServer"
    assert web_server.compute is not None
    assert web_server.compute.type == ComputeType.VM
    assert web_server.compute.instance_count == 1
    assert web_server.tags.get("Name") == "web-server"
    assert web_server.tags.get("Environment") == "production"

    # Verify storage resource
    assert len(storage) == 1
    bucket = storage[0]
    assert bucket.name == "DataBucket"
    assert bucket.storage is not None
    assert bucket.storage.type == StorageType.OBJECT
    assert bucket.tags.get("Environment") == "production"

    # Verify network resource
    assert len(network) == 1
    vpc = network[0]
    assert vpc.name == "MainVPC"
    assert vpc.network is not None
    assert vpc.network.type == NetworkType.VPC
    assert vpc.network.cidr_block == "10.0.0.0/16"
    assert vpc.tags.get("Name") == "main"

    # Verify database resource
    assert len(database) == 1
    db = database[0]
    assert db.name == "Database"
    assert db.database is not None
    assert db.database.type == DatabaseType.RELATIONAL
    assert db.database.engine == "mysql"
    assert db.database.version == "5.7"
    assert db.database.storage_gb == 20
    assert db.database.encryption_required is True
    assert db.database.multi_az is False
    assert db.tags.get("Environment") == "production"


def test_parse_invalid_cloudformation(tmp_path):
    """Test parsing invalid CloudFormation template."""
    # Create invalid template
    invalid_template = {
        "Resources": {
            "WebServer": {
                "Type": "AWS::EC2::Instance",
                # Missing required Properties
            }
        }
    }
    
    template_path = tmp_path / "template.yaml"
    template_path.write_text(yaml.dump(invalid_template))

    # Parsing should raise an error
    with pytest.raises(ValidationError):
        parse_requirements(str(template_path), SourceType.CLOUDFORMATION)


def test_parse_invalid_format(tmp_path):
    """Test parsing template with invalid format."""
    # Create template with invalid format version
    invalid_template = {
        "AWSTemplateFormatVersion": "invalid-version",
        "Resources": {}
    }
    
    template_path = tmp_path / "template.yaml"
    template_path.write_text(yaml.dump(invalid_template))

    # Parsing should raise an error
    with pytest.raises(TemplateFormatError):
        parse_requirements(str(template_path), SourceType.CLOUDFORMATION)


def test_resource_type_identification():
    """Test identification of resource types from CloudFormation resource types."""
    parser = CloudFormationParser("dummy/path")

    # Test compute resources
    assert parser._get_resource_category("AWS::EC2::Instance") == ResourceType.COMPUTE
    assert parser._get_resource_category("AWS::AutoScaling::LaunchConfiguration") == ResourceType.COMPUTE
    assert parser._get_resource_category("AWS::ECS::TaskDefinition") == ResourceType.COMPUTE

    # Test storage resources
    assert parser._get_resource_category("AWS::S3::Bucket") == ResourceType.STORAGE
    assert parser._get_resource_category("AWS::EBS::Volume") == ResourceType.STORAGE
    assert parser._get_resource_category("AWS::EFS::FileSystem") == ResourceType.STORAGE

    # Test network resources
    assert parser._get_resource_category("AWS::EC2::VPC") == ResourceType.NETWORK
    assert parser._get_resource_category("AWS::EC2::Subnet") == ResourceType.NETWORK
    assert parser._get_resource_category("AWS::EC2::SecurityGroup") == ResourceType.NETWORK

    # Test database resources
    assert parser._get_resource_category("AWS::RDS::DBInstance") == ResourceType.DATABASE
    assert parser._get_resource_category("AWS::RDS::DBCluster") == ResourceType.DATABASE
    assert parser._get_resource_category("AWS::DynamoDB::Table") == ResourceType.DATABASE

    # Test unknown resource type
    assert parser._get_resource_category("AWS::Unknown::Resource") is None


def test_dependency_extraction():
    """Test extraction of resource dependencies."""
    parser = CloudFormationParser("dummy/path")

    # Test DependsOn
    resource_data = {
        "Type": "AWS::EC2::Instance",
        "DependsOn": ["MainVPC", "PublicSubnet"]
    }
    deps = parser._extract_dependencies(resource_data)
    assert "MainVPC" in deps
    assert "PublicSubnet" in deps

    # Test Ref and GetAtt in Properties
    resource_data = {
        "Type": "AWS::EC2::Instance",
        "Properties": {
            "VpcId": {"Ref": "MainVPC"},
            "SubnetId": {"Fn::GetAtt": ["PublicSubnet", "SubnetId"]},
            "SecurityGroups": [
                {"Ref": "WebServerSecurityGroup"}
            ]
        }
    }
    deps = parser._extract_dependencies(resource_data)
    assert "MainVPC" in deps
    assert "PublicSubnet" in deps
    assert "WebServerSecurityGroup" in deps


def test_tag_extraction():
    """Test extraction of resource tags."""
    parser = CloudFormationParser("dummy/path")

    # Test CloudFormation tag format
    resource_data = {
        "Properties": {
            "Tags": [
                {"Key": "Name", "Value": "web-server"},
                {"Key": "Environment", "Value": "production"},
                {"Key": "Project", "Value": "demo"}
            ]
        }
    }
    tags = parser._extract_tags(resource_data.get("Properties", {}))
    assert tags["Name"] == "web-server"
    assert tags["Environment"] == "production"
    assert tags["Project"] == "demo"

    # Test empty tags
    resource_data = {"Properties": {}}
    tags = parser._extract_tags(resource_data.get("Properties", {}))
    assert not tags

    # Test invalid tags
    resource_data = {"Properties": {"Tags": "invalid"}}
    tags = parser._extract_tags(resource_data.get("Properties", {}))
    assert not tags


def test_parameter_resolution():
    """Test resolution of template parameters."""
    parser = CloudFormationParser("dummy/path")

    # Parse parameters section
    parameters = {
        "Environment": {
            "Type": "String",
            "Default": "production"
        },
        "InstanceType": {
            "Type": "String",
            "Default": "t2.micro"
        },
        "NoDefault": {
            "Type": "String"
        }
    }
    parser._parse_parameters(parameters)

    # Verify parameter values
    assert parser.parameters["Environment"] == "production"
    assert parser.parameters["InstanceType"] == "t2.micro"
    assert parser.parameters["NoDefault"] is None
