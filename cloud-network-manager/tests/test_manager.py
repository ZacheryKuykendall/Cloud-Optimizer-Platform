"""Tests for the cloud network manager."""

from datetime import datetime
from ipaddress import IPv4Network
from typing import Dict
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cloud_network_manager.exceptions import (
    NetworkCreationError,
    NetworkDeletionError,
    UnsupportedProviderError,
    ValidationError,
    VPNCreationError,
    VPNDeletionError,
)
from cloud_network_manager.manager import CloudNetworkManager
from cloud_network_manager.models import (
    CloudProvider,
    NetworkConfiguration,
    NetworkState,
    NetworkValidationError,
    NetworkValidationResult,
    VPNConnection,
    VPNGatewayConfiguration,
    VPNStatus,
    VPNTunnelConfiguration,
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
def manager(aws_credentials, azure_credentials, gcp_credentials):
    """Create a CloudNetworkManager instance with mock credentials."""
    with patch("cloud_network_manager.vpn_modules.aws_azure.manager.AWSAzureVPNManager"), \
         patch("cloud_network_manager.vpn_modules.azure_gcp.manager.AzureGCPVPNManager"), \
         patch("cloud_network_manager.vpn_modules.aws_gcp.manager.AWSGCPVPNManager"):
        return CloudNetworkManager(
            aws_credentials=aws_credentials,
            azure_credentials=azure_credentials,
            gcp_credentials=gcp_credentials
        )


@pytest.fixture
def network_config():
    """Sample network configuration."""
    return NetworkConfiguration(
        provider=CloudProvider.AWS,
        network_type="vpc",
        name="test-network",
        region="us-east-1",
        cidr_block=IPv4Network("10.0.0.0/16"),
        subnets=[
            IPv4Network("10.0.1.0/24"),
            IPv4Network("10.0.2.0/24")
        ],
        tags={"Environment": "test"}
    )


@pytest.fixture
def vpn_config():
    """Sample VPN configuration."""
    return {
        "source_network": NetworkConfiguration(
            provider=CloudProvider.AWS,
            network_type="vpc",
            name="aws-network",
            region="us-east-1",
            cidr_block=IPv4Network("10.0.0.0/16")
        ),
        "target_network": NetworkConfiguration(
            provider=CloudProvider.AZURE,
            network_type="vnet",
            name="azure-network",
            region="eastus",
            cidr_block=IPv4Network("172.16.0.0/16")
        ),
        "source_gateway": VPNGatewayConfiguration(
            name="aws-gateway",
            type="site_to_site",
            bandwidth="1Gbps",
            availability_zones=["us-east-1a"]
        ),
        "target_gateway": VPNGatewayConfiguration(
            name="azure-gateway",
            type="route_based",
            bandwidth="1Gbps"
        ),
        "tunnels": [
            VPNTunnelConfiguration(
                name="tunnel-1",
                inside_cidr=IPv4Network("169.254.1.0/30")
            )
        ]
    }


def test_initialization(aws_credentials, azure_credentials, gcp_credentials):
    """Test manager initialization."""
    # Test with all providers
    manager = CloudNetworkManager(
        aws_credentials=aws_credentials,
        azure_credentials=azure_credentials,
        gcp_credentials=gcp_credentials
    )
    assert CloudProvider.AWS in manager.providers
    assert CloudProvider.AZURE in manager.providers
    assert CloudProvider.GCP in manager.providers
    assert len(manager.vpn_managers) == 3

    # Test with subset of providers
    manager = CloudNetworkManager(aws_credentials=aws_credentials)
    assert CloudProvider.AWS in manager.providers
    assert CloudProvider.AZURE not in manager.providers
    assert CloudProvider.GCP not in manager.providers
    assert len(manager.vpn_managers) == 0


@pytest.mark.asyncio
async def test_create_network(manager, network_config):
    """Test network creation."""
    # Mock VPN manager
    mock_manager = AsyncMock()
    mock_manager.create_network.return_value = "network-123"
    mock_manager.validate_network_config.return_value = NetworkValidationResult(
        valid=True,
        errors=[],
        warnings=[],
        timestamp=datetime.utcnow()
    )
    manager._get_vpn_manager_for_provider = MagicMock(return_value=mock_manager)

    # Test successful creation
    network_id = await manager.create_network(network_config)
    assert network_id == "network-123"
    mock_manager.create_network.assert_called_once_with(network_config)

    # Test validation failure
    mock_manager.validate_network_config.return_value = NetworkValidationResult(
        valid=False,
        errors=[
            NetworkValidationError(
                resource_id="",
                resource_type="network",
                error_type="validation",
                description="Invalid CIDR",
                severity="high"
            )
        ],
        timestamp=datetime.utcnow()
    )
    with pytest.raises(ValidationError):
        await manager.create_network(network_config)

    # Test unsupported provider
    config = NetworkConfiguration(
        provider=CloudProvider.GCP,
        network_type="vpc_network",
        name="test",
        region="us-central1",
        cidr_block=IPv4Network("10.0.0.0/16")
    )
    manager.providers = {CloudProvider.AWS}  # Only AWS supported
    with pytest.raises(UnsupportedProviderError):
        await manager.create_network(config)


@pytest.mark.asyncio
async def test_delete_network(manager):
    """Test network deletion."""
    # Mock VPN manager
    mock_manager = AsyncMock()
    manager._get_vpn_manager_for_provider = MagicMock(return_value=mock_manager)

    # Test successful deletion
    await manager.delete_network(CloudProvider.AWS, "network-123")
    mock_manager.delete_network.assert_called_once_with("network-123")

    # Test deletion failure
    mock_manager.delete_network.side_effect = Exception("API Error")
    with pytest.raises(NetworkDeletionError):
        await manager.delete_network(CloudProvider.AWS, "network-123")

    # Test unsupported provider
    manager.providers = {CloudProvider.AZURE}  # Only Azure supported
    with pytest.raises(UnsupportedProviderError):
        await manager.delete_network(CloudProvider.AWS, "network-123")


@pytest.mark.asyncio
async def test_create_vpn_connection(manager, vpn_config):
    """Test VPN connection creation."""
    # Mock VPN manager
    mock_manager = AsyncMock()
    mock_manager.create_vpn_connection.return_value = VPNConnection(
        id="vpn-123",
        name="test-vpn",
        source_network=vpn_config["source_network"],
        target_network=vpn_config["target_network"],
        source_gateway=vpn_config["source_gateway"],
        target_gateway=vpn_config["target_gateway"],
        tunnels=vpn_config["tunnels"],
        status=VPNStatus.AVAILABLE
    )
    manager._get_vpn_manager_for_pair = MagicMock(return_value=mock_manager)

    # Test successful creation
    connection = await manager.create_vpn_connection(**vpn_config)
    assert connection.id == "vpn-123"
    mock_manager.create_vpn_connection.assert_called_once_with(**vpn_config)

    # Test creation failure
    mock_manager.create_vpn_connection.side_effect = Exception("API Error")
    with pytest.raises(VPNCreationError):
        await manager.create_vpn_connection(**vpn_config)

    # Test unsupported provider pair
    manager._get_vpn_manager_for_pair.return_value = None
    with pytest.raises(UnsupportedProviderError):
        await manager.create_vpn_connection(**vpn_config)


@pytest.mark.asyncio
async def test_delete_vpn_connection(manager):
    """Test VPN connection deletion."""
    # Mock VPN manager
    mock_manager = AsyncMock()
    manager._get_vpn_manager_for_pair = MagicMock(return_value=mock_manager)

    # Test successful deletion
    await manager.delete_vpn_connection(
        "vpn-123",
        CloudProvider.AWS,
        CloudProvider.AZURE
    )
    mock_manager.delete_vpn_connection.assert_called_once_with("vpn-123")

    # Test deletion failure
    mock_manager.delete_vpn_connection.side_effect = Exception("API Error")
    with pytest.raises(VPNDeletionError):
        await manager.delete_vpn_connection(
            "vpn-123",
            CloudProvider.AWS,
            CloudProvider.AZURE
        )

    # Test unsupported provider pair
    manager._get_vpn_manager_for_pair.return_value = None
    with pytest.raises(UnsupportedProviderError):
        await manager.delete_vpn_connection(
            "vpn-123",
            CloudProvider.AWS,
            CloudProvider.AZURE
        )


@pytest.mark.asyncio
async def test_get_network_state(manager):
    """Test getting network state."""
    # Mock VPN managers
    aws_state = NetworkState(
        networks={"aws-1": NetworkConfiguration(
            provider=CloudProvider.AWS,
            network_type="vpc",
            name="aws-network",
            region="us-east-1",
            cidr_block=IPv4Network("10.0.0.0/16")
        )},
        last_updated=datetime.utcnow()
    )
    azure_state = NetworkState(
        networks={"azure-1": NetworkConfiguration(
            provider=CloudProvider.AZURE,
            network_type="vnet",
            name="azure-network",
            region="eastus",
            cidr_block=IPv4Network("172.16.0.0/16")
        )},
        last_updated=datetime.utcnow()
    )

    mock_aws_manager = AsyncMock()
    mock_aws_manager.get_network_state.return_value = aws_state
    mock_azure_manager = AsyncMock()
    mock_azure_manager.get_network_state.return_value = azure_state

    def get_manager(provider):
        if provider == CloudProvider.AWS:
            return mock_aws_manager
        return mock_azure_manager

    manager._get_vpn_manager_for_provider = MagicMock(side_effect=get_manager)
    manager.providers = {CloudProvider.AWS, CloudProvider.AZURE}

    # Test getting state
    state = await manager.get_network_state()
    assert len(state.networks) == 2
    assert "aws-1" in state.networks
    assert "azure-1" in state.networks


@pytest.mark.asyncio
async def test_validate_network_config(manager, network_config):
    """Test network configuration validation."""
    # Mock VPN manager
    mock_manager = AsyncMock()
    mock_manager.validate_network_config.return_value = NetworkValidationResult(
        valid=True,
        errors=[],
        warnings=[],
        timestamp=datetime.utcnow()
    )
    manager._get_vpn_manager_for_provider = MagicMock(return_value=mock_manager)

    # Test valid configuration
    result = await manager.validate_network_config(network_config)
    assert result.valid
    assert not result.errors
    mock_manager.validate_network_config.assert_called_once_with(network_config)

    # Test invalid configuration
    config = NetworkConfiguration(
        provider=CloudProvider.AWS,
        network_type="vpc",
        name="",  # Invalid: empty name
        region="us-east-1",
        cidr_block=IPv4Network("10.0.0.0/16")
    )
    result = await manager.validate_network_config(config)
    assert not result.valid
    assert len(result.errors) == 1
    assert result.errors[0].error_type == "validation"


def test_get_vpn_manager_for_provider(manager):
    """Test getting VPN manager for a provider."""
    # Test supported provider
    manager.providers = {CloudProvider.AWS}
    manager.vpn_managers = {
        (CloudProvider.AWS, CloudProvider.AZURE): MagicMock()
    }
    assert manager._get_vpn_manager_for_provider(CloudProvider.AWS) is not None

    # Test unsupported provider
    with pytest.raises(UnsupportedProviderError):
        manager._get_vpn_manager_for_provider(CloudProvider.GCP)


def test_get_vpn_manager_for_pair(manager):
    """Test getting VPN manager for a provider pair."""
    mock_manager = MagicMock()
    manager.vpn_managers = {
        (CloudProvider.AWS, CloudProvider.AZURE): mock_manager
    }

    # Test supported pair (normal order)
    result = manager._get_vpn_manager_for_pair(
        CloudProvider.AWS,
        CloudProvider.AZURE
    )
    assert result == mock_manager

    # Test supported pair (reverse order)
    result = manager._get_vpn_manager_for_pair(
        CloudProvider.AZURE,
        CloudProvider.AWS
    )
    assert result == mock_manager

    # Test unsupported pair
    result = manager._get_vpn_manager_for_pair(
        CloudProvider.AWS,
        CloudProvider.GCP
    )
    assert result is None
