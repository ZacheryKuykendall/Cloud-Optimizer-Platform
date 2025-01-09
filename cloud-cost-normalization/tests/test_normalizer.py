"""Tests for the cloud cost normalization service."""

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cloud_cost_normalization.currency import CurrencyService
from cloud_cost_normalization.exceptions import (
    DataNormalizationError,
    ResourceMappingError,
    UnsupportedProviderError,
)
from cloud_cost_normalization.models import (
    BillingType,
    CloudProvider,
    CostAllocation,
    CostBreakdown,
    NormalizedCostEntry,
    ResourceMetadata,
    ResourceType,
)
from cloud_cost_normalization.normalizer import CloudCostNormalizer


@pytest.fixture
def mock_aws_client():
    """Create a mock AWS Cost Explorer client."""
    client = AsyncMock()
    client.get_cost_and_usage = AsyncMock()
    return client


@pytest.fixture
def mock_azure_client():
    """Create a mock Azure Cost Management client."""
    client = AsyncMock()
    client.get_cost_details = AsyncMock()
    return client


@pytest.fixture
def mock_gcp_client():
    """Create a mock GCP Billing client."""
    client = AsyncMock()
    client.get_billing_data = AsyncMock()
    return client


@pytest.fixture
def mock_currency_service():
    """Create a mock currency service."""
    service = MagicMock(spec=CurrencyService)
    service.convert_amount = MagicMock(return_value=Decimal("100.00"))
    return service


@pytest.fixture
def normalizer(
    mock_aws_client,
    mock_azure_client,
    mock_gcp_client,
    mock_currency_service
):
    """Create a CloudCostNormalizer instance with mock clients."""
    return CloudCostNormalizer(
        aws_client=mock_aws_client,
        azure_client=mock_azure_client,
        gcp_client=mock_gcp_client,
        currency_service=mock_currency_service,
        target_currency="USD"
    )


def test_resource_mapping():
    """Test resource type mapping functionality."""
    normalizer = CloudCostNormalizer()

    # Test AWS compute mapping
    aws_mapping = normalizer._get_resource_mapping(
        CloudProvider.AWS,
        "Amazon Elastic Compute Cloud"
    )
    assert aws_mapping.normalized_type == ResourceType.COMPUTE
    assert "instanceType" in aws_mapping.metadata_mapping

    # Test Azure storage mapping
    azure_mapping = normalizer._get_resource_mapping(
        CloudProvider.AZURE,
        "Microsoft.Storage"
    )
    assert azure_mapping.normalized_type == ResourceType.STORAGE
    assert "tier" in azure_mapping.metadata_mapping

    # Test GCP compute mapping
    gcp_mapping = normalizer._get_resource_mapping(
        CloudProvider.GCP,
        "Compute Engine"
    )
    assert gcp_mapping.normalized_type == ResourceType.COMPUTE
    assert "machine_type" in gcp_mapping.metadata_mapping

    # Test invalid mapping
    with pytest.raises(ResourceMappingError):
        normalizer._get_resource_mapping(
            CloudProvider.AWS,
            "Invalid Service"
        )


@pytest.mark.asyncio
async def test_normalize_aws_costs(normalizer, mock_aws_client):
    """Test AWS cost normalization."""
    # Mock AWS cost data
    mock_aws_client.get_cost_and_usage.return_value = {
        "ResultsByTime": [{
            "Groups": [{
                "Keys": ["i-1234567890abcdef0"],
                "Metrics": {
                    "UnblendedCost": 100.00,
                    "ResourceType": "Amazon Elastic Compute Cloud",
                    "ResourceName": "test-instance",
                    "Region": "us-east-1",
                    "instanceType": "t3.micro",
                    "operatingSystem": "Linux",
                    "Tags": {
                        "Environment": "production"
                    }
                }
            }]
        }],
        "AccountId": "123456789012",
        "Currency": "USD"
    }

    # Test normalization
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)
    entries = await normalizer.normalize_costs(
        CloudProvider.AWS,
        start_time,
        end_time
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.resource.provider == CloudProvider.AWS
    assert entry.resource.type == ResourceType.COMPUTE
    assert entry.resource.region == "us-east-1"
    assert entry.resource.specifications["instance_type"] == "t3.micro"
    assert entry.cost_breakdown.compute == Decimal("100.00")


@pytest.mark.asyncio
async def test_normalize_azure_costs(normalizer, mock_azure_client):
    """Test Azure cost normalization."""
    # Mock Azure cost data
    mock_azure_client.get_cost_details.return_value = {
        "properties": {
            "rows": [{
                "resourceId": "/subscriptions/sub-id/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
                "resourceType": "Microsoft.Compute",
                "resourceName": "test-vm",
                "location": "eastus",
                "size": "Standard_B2s",
                "os": "Windows",
                "cost": 150.00,
                "currency": "USD",
                "subscriptionId": "sub-id",
                "tags": {
                    "Environment": "staging"
                }
            }]
        }
    }

    # Test normalization
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)
    entries = await normalizer.normalize_costs(
        CloudProvider.AZURE,
        start_time,
        end_time
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.resource.provider == CloudProvider.AZURE
    assert entry.resource.type == ResourceType.COMPUTE
    assert entry.resource.region == "eastus"
    assert entry.resource.specifications["instance_type"] == "Standard_B2s"
    assert entry.cost_breakdown.compute == Decimal("150.00")


@pytest.mark.asyncio
async def test_normalize_gcp_costs(normalizer, mock_gcp_client):
    """Test GCP cost normalization."""
    # Mock GCP cost data
    mock_gcp_client.get_billing_data.return_value = {
        "billing_data": [{
            "resource": {
                "id": "test-instance-id",
                "name": "test-instance"
            },
            "service": {
                "description": "Compute Engine"
            },
            "location": {
                "region": "us-central1"
            },
            "machine_type": "n1-standard-2",
            "os": "Linux",
            "cost": {
                "amount": 200.00,
                "currency": "USD"
            },
            "billing_account_id": "billing-account-id",
            "project": {
                "id": "test-project"
            },
            "labels": {
                "environment": "development",
                "cost_center": "engineering"
            }
        }]
    }

    # Test normalization
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)
    entries = await normalizer.normalize_costs(
        CloudProvider.GCP,
        start_time,
        end_time
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.resource.provider == CloudProvider.GCP
    assert entry.resource.type == ResourceType.COMPUTE
    assert entry.resource.region == "us-central1"
    assert entry.resource.specifications["instance_type"] == "n1-standard-2"
    assert entry.cost_breakdown.compute == Decimal("200.00")


@pytest.mark.asyncio
async def test_unsupported_provider(normalizer):
    """Test handling of unsupported providers."""
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)

    with pytest.raises(UnsupportedProviderError):
        await normalizer.normalize_costs(
            "INVALID_PROVIDER",  # type: ignore
            start_time,
            end_time
        )


@pytest.mark.asyncio
async def test_provider_not_configured(normalizer):
    """Test handling of unconfigured providers."""
    normalizer.aws_client = None
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)

    with pytest.raises(UnsupportedProviderError):
        await normalizer.normalize_costs(
            CloudProvider.AWS,
            start_time,
            end_time
        )


@pytest.mark.asyncio
async def test_cost_aggregation(normalizer):
    """Test cost aggregation functionality."""
    # Create test entries
    entries = [
        NormalizedCostEntry(
            id="test-1",
            account_id="123",
            resource=ResourceMetadata(
                provider=CloudProvider.AWS,
                provider_id="i-123",
                name="test-instance-1",
                type=ResourceType.COMPUTE,
                region="us-east-1",
                billing_type=BillingType.ON_DEMAND,
            ),
            allocation=CostAllocation(
                project="project-1",
                environment="production"
            ),
            cost_breakdown=CostBreakdown(
                compute=Decimal("100.00")
            ),
            currency="USD",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        ),
        NormalizedCostEntry(
            id="test-2",
            account_id="456",
            resource=ResourceMetadata(
                provider=CloudProvider.AZURE,
                provider_id="vm-456",
                name="test-instance-2",
                type=ResourceType.COMPUTE,
                region="eastus",
                billing_type=BillingType.ON_DEMAND,
            ),
            allocation=CostAllocation(
                project="project-2",
                environment="staging"
            ),
            cost_breakdown=CostBreakdown(
                compute=Decimal("150.00")
            ),
            currency="USD",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        ),
    ]

    # Test aggregation by provider
    aggregation = await normalizer.aggregate_costs(
        entries,
        group_by=["resource.provider"]
    )

    assert len(aggregation.costs) == 2
    assert aggregation.costs["aws"] == Decimal("100.00")
    assert aggregation.costs["azure"] == Decimal("150.00")
    assert aggregation.total_cost == Decimal("250.00")

    # Test aggregation by provider and type
    aggregation = await normalizer.aggregate_costs(
        entries,
        group_by=["resource.provider", "resource.type"]
    )

    assert len(aggregation.costs) == 2
    assert aggregation.costs["aws:compute"] == Decimal("100.00")
    assert aggregation.costs["azure:compute"] == Decimal("150.00")
    assert aggregation.total_cost == Decimal("250.00")


@pytest.mark.asyncio
async def test_currency_conversion(normalizer, mock_currency_service):
    """Test currency conversion during normalization."""
    # Mock AWS cost data with non-USD currency
    normalizer.aws_client.get_cost_and_usage.return_value = {
        "ResultsByTime": [{
            "Groups": [{
                "Keys": ["i-1234567890abcdef0"],
                "Metrics": {
                    "UnblendedCost": 100.00,
                    "ResourceType": "Amazon Elastic Compute Cloud",
                    "ResourceName": "test-instance",
                    "Region": "us-east-1",
                }
            }]
        }],
        "Currency": "EUR"
    }

    # Test normalization with currency conversion
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)
    entries = await normalizer.normalize_costs(
        CloudProvider.AWS,
        start_time,
        end_time
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.currency == "USD"
    # Mock currency service was configured to return 100.00
    assert entry.cost_breakdown.compute == Decimal("100.00")
    mock_currency_service.convert_amount.assert_called_once()


def test_invalid_resource_mapping():
    """Test handling of invalid resource mappings."""
    normalizer = CloudCostNormalizer()

    with pytest.raises(ResourceMappingError) as exc_info:
        normalizer._get_resource_mapping(
            CloudProvider.AWS,
            "Invalid Service"
        )

    assert "No mapping found" in str(exc_info.value)
    assert exc_info.value.provider == "aws"
    assert exc_info.value.provider_type == "Invalid Service"
    assert isinstance(exc_info.value.available_mappings, list)
