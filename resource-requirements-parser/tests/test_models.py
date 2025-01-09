"""Tests for the data models."""

import pytest
from datetime import datetime
from uuid import UUID

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
    ParsingResult,
)


def test_compute_requirements():
    """Test ComputeRequirements model."""
    # Test valid requirements
    compute = ComputeRequirements(
        type=ComputeType.VM,
        vcpus=2,
        memory_gb=4.0,
        instance_count=3,
        availability_zones=["us-west-2a", "us-west-2b"],
        operating_system="Linux",
    )
    assert compute.type == ComputeType.VM
    assert compute.vcpus == 2
    assert compute.memory_gb == 4.0
    assert compute.instance_count == 3
    assert compute.availability_zones == ["us-west-2a", "us-west-2b"]
    assert compute.operating_system == "Linux"

    # Test optional fields
    compute = ComputeRequirements(
        type=ComputeType.VM,
        vcpus=2,
        memory_gb=4.0,
    )
    assert compute.instance_count == 1  # Default value
    assert compute.gpu_count is None
    assert compute.availability_zones is None

    # Test validation
    with pytest.raises(ValueError):
        ComputeRequirements(
            type=ComputeType.VM,
            vcpus=0,  # Invalid: must be positive
            memory_gb=4.0,
        )

    with pytest.raises(ValueError):
        ComputeRequirements(
            type=ComputeType.VM,
            vcpus=2,
            memory_gb=-1.0,  # Invalid: must be positive
        )


def test_storage_requirements():
    """Test StorageRequirements model."""
    # Test valid requirements
    storage = StorageRequirements(
        type=StorageType.BLOCK,
        capacity_gb=100.0,
        iops=3000,
        throughput_mbps=125.0,
        encryption_required=True,
        backup_required=True,
        replication_required=False,
    )
    assert storage.type == StorageType.BLOCK
    assert storage.capacity_gb == 100.0
    assert storage.iops == 3000
    assert storage.throughput_mbps == 125.0
    assert storage.encryption_required is True
    assert storage.backup_required is True
    assert storage.replication_required is False

    # Test optional fields
    storage = StorageRequirements(
        type=StorageType.OBJECT,
        capacity_gb=1000.0,
    )
    assert storage.iops is None
    assert storage.throughput_mbps is None
    assert storage.encryption_required is False  # Default value

    # Test validation
    with pytest.raises(ValueError):
        StorageRequirements(
            type=StorageType.BLOCK,
            capacity_gb=-100.0,  # Invalid: must be positive
        )


def test_network_requirements():
    """Test NetworkRequirements model."""
    # Test valid requirements
    network = NetworkRequirements(
        type=NetworkType.VPC,
        cidr_block="10.0.0.0/16",
        port_ranges=[{"from_port": 80, "to_port": 80}],
        protocols=["tcp", "udp"],
        public_access=True,
        vpn_required=True,
    )
    assert network.type == NetworkType.VPC
    assert network.cidr_block == "10.0.0.0/16"
    assert network.port_ranges == [{"from_port": 80, "to_port": 80}]
    assert network.protocols == ["tcp", "udp"]
    assert network.public_access is True
    assert network.vpn_required is True

    # Test optional fields
    network = NetworkRequirements(
        type=NetworkType.SUBNET,
    )
    assert network.cidr_block is None
    assert network.port_ranges is None
    assert network.public_access is False  # Default value


def test_database_requirements():
    """Test DatabaseRequirements model."""
    # Test valid requirements
    database = DatabaseRequirements(
        type=DatabaseType.RELATIONAL,
        engine="mysql",
        version="5.7",
        storage_gb=100.0,
        multi_az=True,
        backup_retention_days=7,
        encryption_required=True,
    )
    assert database.type == DatabaseType.RELATIONAL
    assert database.engine == "mysql"
    assert database.version == "5.7"
    assert database.storage_gb == 100.0
    assert database.multi_az is True
    assert database.backup_retention_days == 7
    assert database.encryption_required is True

    # Test optional fields
    database = DatabaseRequirements(
        type=DatabaseType.NOSQL,
        engine="mongodb",
        version="4.0",
        storage_gb=50.0,
    )
    assert database.multi_az is False  # Default value
    assert database.backup_retention_days is None
    assert database.encryption_required is True  # Default value

    # Test validation
    with pytest.raises(ValueError):
        DatabaseRequirements(
            type=DatabaseType.RELATIONAL,
            engine="mysql",
            version="5.7",
            storage_gb=-100.0,  # Invalid: must be positive
        )


def test_resource_requirements():
    """Test ResourceRequirements model."""
    # Test compute resource
    compute_resource = ResourceRequirements(
        name="web_server",
        type=ResourceType.COMPUTE,
        compute=ComputeRequirements(
            type=ComputeType.VM,
            vcpus=2,
            memory_gb=4.0,
        ),
        tags={"Name": "web-server", "Environment": "production"},
        dependencies=["vpc", "subnet"],
    )
    assert compute_resource.name == "web_server"
    assert compute_resource.type == ResourceType.COMPUTE
    assert compute_resource.compute is not None
    assert compute_resource.storage is None
    assert compute_resource.tags["Name"] == "web-server"
    assert "vpc" in compute_resource.dependencies

    # Test validation of required fields
    with pytest.raises(ValueError):
        ResourceRequirements(
            name="web_server",
            type=ResourceType.COMPUTE,
            # Missing required compute field for compute resource
        )


def test_infrastructure_requirements():
    """Test InfrastructureRequirements model."""
    # Create some resources
    web_server = ResourceRequirements(
        name="web_server",
        type=ResourceType.COMPUTE,
        compute=ComputeRequirements(
            type=ComputeType.VM,
            vcpus=2,
            memory_gb=4.0,
        ),
    )
    
    database = ResourceRequirements(
        name="database",
        type=ResourceType.DATABASE,
        database=DatabaseRequirements(
            type=DatabaseType.RELATIONAL,
            engine="mysql",
            version="5.7",
            storage_gb=100.0,
        ),
        dependencies=["web_server"],
    )

    # Create infrastructure requirements
    infra = InfrastructureRequirements(
        name="test_infrastructure",
        source_type=SourceType.TERRAFORM,
        source_path="/path/to/terraform",
        resources=[web_server, database],
        global_tags={"Project": "test"},
    )

    # Test basic attributes
    assert infra.name == "test_infrastructure"
    assert infra.source_type == SourceType.TERRAFORM
    assert len(infra.resources) == 2
    assert isinstance(infra.id, UUID)
    assert isinstance(infra.creation_time, datetime)

    # Test helper methods
    assert infra.get_resource_by_name("web_server") == web_server
    assert infra.get_resource_by_name("nonexistent") is None

    compute_resources = infra.get_resources_by_type(ResourceType.COMPUTE)
    assert len(compute_resources) == 1
    assert compute_resources[0] == web_server

    dependent_resources = infra.get_dependent_resources("web_server")
    assert len(dependent_resources) == 1
    assert dependent_resources[0] == database

    dependencies = infra.get_dependencies("database")
    assert len(dependencies) == 1
    assert dependencies[0] == web_server


def test_parsing_result():
    """Test ParsingResult model."""
    # Create a simple infrastructure
    infra = InfrastructureRequirements(
        name="test_infrastructure",
        source_type=SourceType.TERRAFORM,
        source_path="/path/to/terraform",
        resources=[
            ResourceRequirements(
                name="web_server",
                type=ResourceType.COMPUTE,
                compute=ComputeRequirements(
                    type=ComputeType.VM,
                    vcpus=2,
                    memory_gb=4.0,
                ),
            ),
        ],
    )

    # Create parsing result
    result = ParsingResult(
        requirements=infra,
        warnings=["Missing tags"],
        errors=[],
        metadata={"parser_version": "1.0.0"},
    )

    assert result.requirements == infra
    assert len(result.warnings) == 1
    assert not result.errors
    assert result.metadata["parser_version"] == "1.0.0"
