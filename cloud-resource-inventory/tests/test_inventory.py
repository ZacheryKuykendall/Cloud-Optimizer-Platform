"""Tests for the cloud resource inventory manager."""

from datetime import datetime, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cloud_resource_inventory.exceptions import (
    GroupAlreadyExistsError,
    GroupNotFoundError,
    InvalidQueryError,
    ResourceNotFoundError,
    TagLimitExceededError,
    TagValidationError,
    UnsupportedProviderError,
    ValidationError,
)
from cloud_resource_inventory.inventory import ResourceInventoryManager
from cloud_resource_inventory.models import (
    CloudProvider,
    Resource,
    ResourceConfiguration,
    ResourceCost,
    ResourceCriticality,
    ResourceGroup,
    ResourceLifecycle,
    ResourceMetadata,
    ResourceMonitoring,
    ResourceQuery,
    ResourceStatus,
    ResourceTag,
    ResourceType,
)


@pytest.fixture
def aws_credentials():
    """Sample AWS credentials."""
    return {
        "aws_access_key_id": "test-key",
        "aws_secret_access_key": "test-secret",
        "region": "us-east-1"
    }


@pytest.fixture
def azure_credentials():
    """Sample Azure credentials."""
    return {
        "subscription_id": "test-sub",
        "tenant_id": "test-tenant",
        "client_id": "test-client",
        "client_secret": "test-secret"
    }


@pytest.fixture
def gcp_credentials():
    """Sample GCP credentials."""
    return {
        "project_id": "test-project",
        "credentials_path": "/path/to/credentials.json"
    }


@pytest.fixture
def inventory_manager(aws_credentials, azure_credentials, gcp_credentials):
    """Create a ResourceInventoryManager instance with mock clients."""
    with patch("cloud_resource_inventory.inventory.ResourceInventoryManager._init_aws_client"), \
         patch("cloud_resource_inventory.inventory.ResourceInventoryManager._init_azure_client"), \
         patch("cloud_resource_inventory.inventory.ResourceInventoryManager._init_gcp_client"):
        return ResourceInventoryManager(
            aws_credentials=aws_credentials,
            azure_credentials=azure_credentials,
            gcp_credentials=gcp_credentials
        )


@pytest.fixture
def sample_resource():
    """Create a sample resource."""
    return Resource(
        id="res-123",
        name="test-resource",
        provider=CloudProvider.AWS,
        type=ResourceType.COMPUTE,
        region="us-east-1",
        status=ResourceStatus.ACTIVE,
        lifecycle=ResourceLifecycle.PRODUCTION,
        criticality=ResourceCriticality.HIGH,
        metadata=ResourceMetadata(
            created_by="test-user",
            created_at=datetime.utcnow()
        ),
        configuration=ResourceConfiguration(),
        monitoring=ResourceMonitoring(),
        cost=ResourceCost(
            hourly_cost=0.10,
            monthly_cost=73.00
        )
    )


def test_initialization(aws_credentials, azure_credentials, gcp_credentials):
    """Test manager initialization."""
    # Test with all providers
    manager = ResourceInventoryManager(
        aws_credentials=aws_credentials,
        azure_credentials=azure_credentials,
        gcp_credentials=gcp_credentials
    )
    assert CloudProvider.AWS in manager.providers
    assert CloudProvider.AZURE in manager.providers
    assert CloudProvider.GCP in manager.providers
    assert manager.max_tags_per_resource == 50

    # Test with subset of providers
    manager = ResourceInventoryManager(aws_credentials=aws_credentials)
    assert CloudProvider.AWS in manager.providers
    assert CloudProvider.AZURE not in manager.providers
    assert CloudProvider.GCP not in manager.providers

    # Test with no providers
    with pytest.raises(ValidationError):
        ResourceInventoryManager()

    # Test with custom tag limit
    manager = ResourceInventoryManager(
        aws_credentials=aws_credentials,
        max_tags_per_resource=10
    )
    assert manager.max_tags_per_resource == 10


@pytest.mark.asyncio
async def test_discover_resources(inventory_manager, sample_resource):
    """Test resource discovery."""
    # Mock provider discovery
    inventory_manager._discover_provider_resources = AsyncMock(
        return_value=[sample_resource]
    )

    # Test successful discovery
    resources = await inventory_manager.discover_resources(
        providers=[CloudProvider.AWS],
        resource_types=[ResourceType.COMPUTE],
        regions=["us-east-1"]
    )
    assert len(resources) == 1
    assert resources[0].id == sample_resource.id
    assert len(inventory_manager.state.resources) == 1

    # Test with unsupported provider
    with pytest.raises(UnsupportedProviderError):
        await inventory_manager.discover_resources(
            providers=["unknown"]
        )


@pytest.mark.asyncio
async def test_get_resource(inventory_manager, sample_resource):
    """Test resource retrieval."""
    # Add resource to state
    inventory_manager.state.resources[sample_resource.id] = sample_resource

    # Test successful retrieval
    resource = await inventory_manager.get_resource(sample_resource.id)
    assert resource.id == sample_resource.id
    assert resource.name == sample_resource.name

    # Test with non-existent resource
    with pytest.raises(ResourceNotFoundError):
        await inventory_manager.get_resource("non-existent")


@pytest.mark.asyncio
async def test_update_resource(inventory_manager, sample_resource):
    """Test resource updates."""
    # Add resource to state
    inventory_manager.state.resources[sample_resource.id] = sample_resource
    inventory_manager._update_provider_resource = AsyncMock()

    # Test successful update
    updates = {
        "name": "updated-name",
        "status": ResourceStatus.STOPPED
    }
    updated = await inventory_manager.update_resource(sample_resource.id, updates)
    assert updated.name == "updated-name"
    assert updated.status == ResourceStatus.STOPPED

    # Test with non-existent resource
    with pytest.raises(ResourceNotFoundError):
        await inventory_manager.update_resource("non-existent", updates)


@pytest.mark.asyncio
async def test_delete_resource(inventory_manager, sample_resource):
    """Test resource deletion."""
    # Add resource to state
    inventory_manager.state.resources[sample_resource.id] = sample_resource
    inventory_manager._delete_provider_resource = AsyncMock()

    # Test successful deletion
    await inventory_manager.delete_resource(sample_resource.id)
    assert sample_resource.id not in inventory_manager.state.resources

    # Test with non-existent resource
    with pytest.raises(ResourceNotFoundError):
        await inventory_manager.delete_resource("non-existent")


@pytest.mark.asyncio
async def test_tag_resource(inventory_manager, sample_resource):
    """Test resource tagging."""
    # Add resource to state
    inventory_manager.state.resources[sample_resource.id] = sample_resource
    inventory_manager._update_provider_tags = AsyncMock()

    # Test successful tagging
    tags = {"env": "prod", "team": "platform"}
    tagged = await inventory_manager.tag_resource(sample_resource.id, tags)
    assert "env" in tagged.tags
    assert tagged.tags["env"].value == "prod"

    # Test tag limit
    inventory_manager.max_tags_per_resource = 1
    with pytest.raises(TagLimitExceededError):
        await inventory_manager.tag_resource(sample_resource.id, {"key1": "val1", "key2": "val2"})

    # Test invalid tags
    inventory_manager._is_valid_tag = MagicMock(return_value=False)
    with pytest.raises(TagValidationError):
        await inventory_manager.tag_resource(sample_resource.id, {"invalid": "tag"})


@pytest.mark.asyncio
async def test_create_group(inventory_manager):
    """Test group creation."""
    # Test successful creation
    group = await inventory_manager.create_group(
        name="test-group",
        description="Test group",
        tags={"env": "prod"}
    )
    assert group.name == "test-group"
    assert group.description == "Test group"
    assert "env" in group.tags

    # Test duplicate group
    with pytest.raises(GroupAlreadyExistsError):
        await inventory_manager.create_group("test-group")


@pytest.mark.asyncio
async def test_add_to_group(inventory_manager, sample_resource):
    """Test adding resources to group."""
    # Create group and add resource to state
    group = await inventory_manager.create_group("test-group")
    inventory_manager.state.resources[sample_resource.id] = sample_resource

    # Test successful addition
    updated = await inventory_manager.add_to_group(group.id, [sample_resource.id])
    assert sample_resource.id in updated.resources

    # Test with non-existent group
    with pytest.raises(GroupNotFoundError):
        await inventory_manager.add_to_group("non-existent", [sample_resource.id])

    # Test with non-existent resource
    with pytest.raises(ResourceNotFoundError):
        await inventory_manager.add_to_group(group.id, ["non-existent"])


@pytest.mark.asyncio
async def test_query_resources(inventory_manager, sample_resource):
    """Test resource querying."""
    # Add resource to state
    inventory_manager.state.resources[sample_resource.id] = sample_resource

    # Test query by provider
    query = ResourceQuery(providers=[CloudProvider.AWS])
    results = await inventory_manager.query_resources(query)
    assert len(results) == 1
    assert results[0].id == sample_resource.id

    # Test query by type
    query = ResourceQuery(types=[ResourceType.COMPUTE])
    results = await inventory_manager.query_resources(query)
    assert len(results) == 1

    # Test query by status
    query = ResourceQuery(statuses=[ResourceStatus.ACTIVE])
    results = await inventory_manager.query_resources(query)
    assert len(results) == 1

    # Test query by lifecycle
    query = ResourceQuery(lifecycles=[ResourceLifecycle.PRODUCTION])
    results = await inventory_manager.query_resources(query)
    assert len(results) == 1

    # Test query by criticality
    query = ResourceQuery(criticalities=[ResourceCriticality.HIGH])
    results = await inventory_manager.query_resources(query)
    assert len(results) == 1

    # Test query by tags
    sample_resource.tags["env"] = ResourceTag(key="env", value="prod")
    query = ResourceQuery(tags={"env": "prod"})
    results = await inventory_manager.query_resources(query)
    assert len(results) == 1

    # Test query by creation time
    query = ResourceQuery(
        created_after=datetime.utcnow() - timedelta(hours=1),
        created_before=datetime.utcnow() + timedelta(hours=1)
    )
    results = await inventory_manager.query_resources(query)
    assert len(results) == 1

    # Test query with no matches
    query = ResourceQuery(providers=[CloudProvider.AZURE])
    results = await inventory_manager.query_resources(query)
    assert len(results) == 0


def test_update_summary(inventory_manager, sample_resource):
    """Test summary statistics update."""
    # Add resource to state
    inventory_manager.state.resources[sample_resource.id] = sample_resource

    # Update summary
    inventory_manager._update_summary()
    summary = inventory_manager.state.summary

    assert summary.total_resources == 1
    assert summary.resources_by_provider[CloudProvider.AWS] == 1
    assert summary.resources_by_type[ResourceType.COMPUTE] == 1
    assert summary.resources_by_status[ResourceStatus.ACTIVE] == 1
    assert summary.resources_by_lifecycle[ResourceLifecycle.PRODUCTION] == 1
    assert summary.resources_by_criticality[ResourceCriticality.HIGH] == 1
    assert summary.total_cost["USD"] == 73.00  # Monthly cost
