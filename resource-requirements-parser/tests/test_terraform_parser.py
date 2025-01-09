"""Tests for the Terraform parser implementation."""

import os
from pathlib import Path
import pytest
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
)
from resource_requirements_parser.parsers.terraform import TerraformParser


@pytest.fixture
def temp_terraform_dir(tmp_path):
    """Create a temporary directory with Terraform files."""
    # Create main.tf with various resource types
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

    # Write files
    tf_dir = tmp_path / "terraform"
    tf_dir.mkdir()
    (tf_dir / "main.tf").write_text(main_tf)
    (tf_dir / "variables.tf").write_text(variables_tf)

    return tf_dir


def test_terraform_parser_initialization():
    """Test that the parser can be initialized with a path."""
    parser = TerraformParser("dummy/path")
    assert parser.get_source_type() == SourceType.TERRAFORM


def test_parse_terraform_files(temp_terraform_dir):
    """Test parsing a complete Terraform configuration."""
    result = parse_requirements(str(temp_terraform_dir), SourceType.TERRAFORM)
    
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
    assert web_server.name == "aws_instance.web"
    assert web_server.compute is not None
    assert web_server.compute.type == ComputeType.VM
    assert web_server.compute.instance_count == 1
    assert web_server.tags.get("Name") == "web-server"
    assert web_server.tags.get("Environment") == "production"

    # Verify storage resource
    assert len(storage) == 1
    bucket = storage[0]
    assert bucket.name == "aws_s3_bucket.data"
    assert bucket.storage is not None
    assert bucket.storage.type == StorageType.OBJECT
    assert bucket.tags.get("Environment") == "production"

    # Verify network resource
    assert len(network) == 1
    vpc = network[0]
    assert vpc.name == "aws_vpc.main"
    assert vpc.network is not None
    assert vpc.network.type == NetworkType.VPC
    assert vpc.network.cidr_block == "10.0.0.0/16"
    assert vpc.tags.get("Name") == "main"

    # Verify database resource
    assert len(database) == 1
    db = database[0]
    assert db.name == "aws_db_instance.database"
    assert db.database is not None
    assert db.database.type == DatabaseType.RELATIONAL
    assert db.database.engine == "mysql"
    assert db.database.version == "5.7"
    assert db.database.storage_gb == 20
    assert db.database.encryption_required is True
    assert db.database.multi_az is False
    assert db.tags.get("Environment") == "production"


def test_parse_invalid_terraform(tmp_path):
    """Test parsing invalid Terraform configuration."""
    # Create invalid Terraform file
    invalid_tf = dedent("""
        resource "aws_instance" "web" {
          # Missing required fields
        }
    """)
    
    tf_dir = tmp_path / "terraform"
    tf_dir.mkdir()
    (tf_dir / "main.tf").write_text(invalid_tf)

    # Parsing should raise an error
    with pytest.raises(ValidationError):
        parse_requirements(str(tf_dir), SourceType.TERRAFORM)


def test_parse_missing_terraform(tmp_path):
    """Test parsing a directory with no Terraform files."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # Parsing should raise an error
    with pytest.raises(ParsingError):
        parse_requirements(str(empty_dir), SourceType.TERRAFORM)


def test_resource_type_identification():
    """Test identification of resource types from Terraform resource types."""
    parser = TerraformParser("dummy/path")

    # Test compute resources
    assert parser._get_resource_category("aws_instance") == ResourceType.COMPUTE
    assert parser._get_resource_category("azurerm_virtual_machine") == ResourceType.COMPUTE
    assert parser._get_resource_category("google_compute_instance") == ResourceType.COMPUTE

    # Test storage resources
    assert parser._get_resource_category("aws_s3_bucket") == ResourceType.STORAGE
    assert parser._get_resource_category("azurerm_storage_account") == ResourceType.STORAGE
    assert parser._get_resource_category("google_storage_bucket") == ResourceType.STORAGE

    # Test network resources
    assert parser._get_resource_category("aws_vpc") == ResourceType.NETWORK
    assert parser._get_resource_category("azurerm_virtual_network") == ResourceType.NETWORK
    assert parser._get_resource_category("google_compute_network") == ResourceType.NETWORK

    # Test database resources
    assert parser._get_resource_category("aws_db_instance") == ResourceType.DATABASE
    assert parser._get_resource_category("azurerm_sql_server") == ResourceType.DATABASE
    assert parser._get_resource_category("google_sql_database_instance") == ResourceType.DATABASE

    # Test unknown resource type
    assert parser._get_resource_category("unknown_resource_type") is None


def test_dependency_extraction():
    """Test extraction of resource dependencies."""
    parser = TerraformParser("dummy/path")

    # Test explicit depends_on
    resource_data = {
        "depends_on": ["aws_vpc.main", "aws_subnet.primary"]
    }
    deps = parser._extract_dependencies(resource_data)
    assert "aws_vpc.main" in deps
    assert "aws_subnet.primary" in deps

    # Test implicit dependencies in properties
    resource_data = {
        "properties": {
            "vpc_id": {"Ref": "aws_vpc.main"},
            "subnet_ids": [
                {"Fn::GetAtt": ["aws_subnet.primary", "id"]},
                {"Fn::GetAtt": ["aws_subnet.secondary", "id"]}
            ]
        }
    }
    deps = parser._extract_dependencies(resource_data)
    assert "aws_vpc.main" in deps
    assert "aws_subnet.primary" in deps
    assert "aws_subnet.secondary" in deps


def test_tag_extraction():
    """Test extraction of resource tags."""
    parser = TerraformParser("dummy/path")

    # Test direct tags
    resource_data = {
        "tags": {
            "Name": "web-server",
            "Environment": "production",
            "Project": "demo"
        }
    }
    tags = parser._extract_tags(resource_data)
    assert tags["Name"] == "web-server"
    assert tags["Environment"] == "production"
    assert tags["Project"] == "demo"

    # Test empty tags
    resource_data = {}
    tags = parser._extract_tags(resource_data)
    assert not tags

    # Test invalid tags
    resource_data = {"tags": "invalid"}
    tags = parser._extract_tags(resource_data)
    assert not tags
