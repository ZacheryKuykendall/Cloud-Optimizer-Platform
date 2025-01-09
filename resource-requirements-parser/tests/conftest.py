"""Shared test fixtures and configuration."""

import os
from pathlib import Path
import pytest
from textwrap import dedent

from resource_requirements_parser.models import (
    ResourceType,
    ComputeType,
    StorageType,
    NetworkType,
    DatabaseType,
    SourceType,
    ComputeRequirements,
    StorageRequirements,
    NetworkRequirements,
    DatabaseRequirements,
    ResourceRequirements,
    InfrastructureRequirements,
)


@pytest.fixture
def sample_compute_requirements():
    """Create sample compute requirements for testing."""
    return ComputeRequirements(
        type=ComputeType.VM,
        vcpus=2,
        memory_gb=4.0,
        instance_count=1,
        operating_system="Linux",
        availability_zones=["us-west-2a"],
        custom_requirements={
            "instance_type": "t2.micro"
        }
    )


@pytest.fixture
def sample_storage_requirements():
    """Create sample storage requirements for testing."""
    return StorageRequirements(
        type=StorageType.BLOCK,
        capacity_gb=100.0,
        iops=3000,
        throughput_mbps=125.0,
        encryption_required=True,
        backup_required=True,
        custom_requirements={
            "volume_type": "gp3"
        }
    )


@pytest.fixture
def sample_network_requirements():
    """Create sample network requirements for testing."""
    return NetworkRequirements(
        type=NetworkType.VPC,
        cidr_block="10.0.0.0/16",
        port_ranges=[
            {"from_port": 80, "to_port": 80},
            {"from_port": 443, "to_port": 443}
        ],
        protocols=["tcp"],
        public_access=True,
        custom_requirements={
            "enable_dns": True
        }
    )


@pytest.fixture
def sample_database_requirements():
    """Create sample database requirements for testing."""
    return DatabaseRequirements(
        type=DatabaseType.RELATIONAL,
        engine="mysql",
        version="5.7",
        storage_gb=100.0,
        multi_az=True,
        backup_retention_days=7,
        custom_requirements={
            "instance_class": "db.t3.micro"
        }
    )


@pytest.fixture
def sample_resource_requirements(
    sample_compute_requirements,
    sample_storage_requirements,
    sample_network_requirements,
    sample_database_requirements
):
    """Create sample resource requirements for testing."""
    return {
        "compute": ResourceRequirements(
            name="web_server",
            type=ResourceType.COMPUTE,
            compute=sample_compute_requirements,
            tags={"Name": "web-server", "Environment": "production"},
            dependencies=["vpc", "subnet"]
        ),
        "storage": ResourceRequirements(
            name="data_volume",
            type=ResourceType.STORAGE,
            storage=sample_storage_requirements,
            tags={"Name": "data-volume", "Environment": "production"},
            dependencies=["web_server"]
        ),
        "network": ResourceRequirements(
            name="main_vpc",
            type=ResourceType.NETWORK,
            network=sample_network_requirements,
            tags={"Name": "main-vpc", "Environment": "production"}
        ),
        "database": ResourceRequirements(
            name="main_db",
            type=ResourceType.DATABASE,
            database=sample_database_requirements,
            tags={"Name": "main-db", "Environment": "production"},
            dependencies=["vpc", "subnet"]
        )
    }


@pytest.fixture
def sample_infrastructure_requirements(sample_resource_requirements):
    """Create sample infrastructure requirements for testing."""
    return InfrastructureRequirements(
        name="test_infrastructure",
        source_type=SourceType.TERRAFORM,
        source_path="/path/to/terraform",
        resources=list(sample_resource_requirements.values()),
        global_tags={"Project": "test", "Environment": "production"}
    )


@pytest.fixture
def terraform_test_dir(tmp_path):
    """Create a temporary directory with Terraform test files."""
    tf_dir = tmp_path / "terraform"
    tf_dir.mkdir()

    # Create main.tf
    main_tf = dedent("""
        provider "aws" {
          region = "us-west-2"
        }

        resource "aws_instance" "web" {
          ami           = "ami-0c55b159cbfafe1f0"
          instance_type = "t2.micro"

          tags = {
            Name = "web-server"
            Environment = "production"
          }
        }

        resource "aws_s3_bucket" "data" {
          bucket = "my-data-bucket"
          
          tags = {
            Environment = "production"
          }
        }

        resource "aws_vpc" "main" {
          cidr_block = "10.0.0.0/16"
          
          tags = {
            Name = "main"
          }
        }

        resource "aws_db_instance" "database" {
          engine               = "mysql"
          engine_version       = "5.7"
          instance_class       = "db.t2.micro"
          allocated_storage    = 20
          storage_encrypted    = true
          multi_az            = false
          
          tags = {
            Environment = "production"
          }
        }
    """)
    (tf_dir / "main.tf").write_text(main_tf)

    # Create variables.tf
    variables_tf = dedent("""
        variable "environment" {
          type    = string
          default = "production"
        }

        variable "instance_type" {
          type    = string
          default = "t2.micro"
        }
    """)
    (tf_dir / "variables.tf").write_text(variables_tf)

    return tf_dir


@pytest.fixture
def cloudformation_test_dir(tmp_path):
    """Create a temporary directory with CloudFormation test files."""
    cf_dir = tmp_path / "cloudformation"
    cf_dir.mkdir()

    # Create template.yaml
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

    import yaml
    (cf_dir / "template.yaml").write_text(yaml.dump(template))

    return cf_dir


@pytest.fixture
def test_file_content():
    """Create sample file content for testing."""
    return "Test file content"


@pytest.fixture
def test_file(tmp_path, test_file_content):
    """Create a test file with content."""
    test_file = tmp_path / "test.txt"
    test_file.write_text(test_file_content)
    return test_file


@pytest.fixture
def test_dir(tmp_path):
    """Create a test directory structure."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Create some subdirectories
    (test_dir / "subdir1").mkdir()
    (test_dir / "subdir2").mkdir()
    
    # Create some files
    (test_dir / "file1.txt").write_text("File 1")
    (test_dir / "file2.txt").write_text("File 2")
    (test_dir / "subdir1/file3.txt").write_text("File 3")
    
    return test_dir
